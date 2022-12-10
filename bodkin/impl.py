import itertools
import inspect
from dataclasses import dataclass, field
from abc import abstractmethod

from .core import Ref, RefMap, Node, UninitializedRefError, NestedRefWarning
from .viz import (
    dot_to_html,
    gen_node_dot,
    gen_dag_dot,
    NodeInfo,
    RefInfo,
    PortKind,
    PortInfo,
    DAGInfo,
    show_in_webbrowser,
)


__all__ = [
    "Ref",
    "RefMap",
    "Node",
    "Atom",
    "simple_atom",
    "DAG",
    "toposort",
    "CycleError",
    "UninitializedRefError",
    "NestedRefWarning",
]


class CycleError(Exception):
    """Indicates that a cycle was found in a DAG"""

    pass


def toposort(nodes, edges):
    """Topologically sort the nodes in a directed acyclic graph (DAG)

    The nodes are sorted such that for any pair of nodes X and Y where
    there exists an edge from X to Y, X comes before Y after sorting.

    Arguments:
        nodes: list
            The list of objects to be sorted
        edges: list
            A list of tuples. Each tuple consists of two indices into
            nodes, indicating that there is an edge from the first
            element to the second element

    Returns:
        sorted_nodes: list
            A list containing the same items as nodes, topologically
            sorted

    Raises:
        If the graph contains a cycle, a CycleError is raised

    """
    children = [[] for _ in nodes]
    for src, dst in edges:
        children[src].append(dst)

    processed = set()
    active = set()
    sorted_nodes = []

    def visit(i):
        if i in processed:
            return
        if i in active:
            raise CycleError("Cycle detected")

        active.add(i)

        for ch in children[i]:
            visit(ch)

        active.remove(i)
        processed.add(i)
        sorted_nodes.append(i)

    for i in range(len(nodes)):
        visit(i)

    return [nodes[i] for i in reversed(sorted_nodes)]


class Atom(Node):
    def __init__(self):
        self.__inputs = RefMap()
        self.__outputs = RefMap()

    @abstractmethod
    def _evaluate(self, **kwargs) -> dict | None:
        pass

    def __call__(self):
        result = self._evaluate(**self.i)
        if result:
            self.o |= result

    @property
    def i(self):
        try:
            return self.__inputs
        except AttributeError as err:
            raise RuntimeError("Node is not initialized") from err

    @i.setter
    def i(self, refmap):
        # setter needed to support |= operator
        if refmap is not self.__inputs:
            raise ValueError("Cannot set new RefMap")

    @property
    def o(self):
        try:
            return self.__outputs
        except AttributeError as err:
            raise RuntimeError("Node is not initialized") from err

    @o.setter
    def o(self, refmap):
        # setter needed to support |= operator
        if refmap is not self.__outputs:
            raise ValueError("Cannot set new RefMap")

    def show(self):
        node_info = self._create_info()
        dot_src = gen_node_dot(node_info)
        html_src = dot_to_html(dot_src, title=type(self).__name__)
        show_in_webbrowser(html_src.encode())

    def _create_inputs(self, *keys: list[str]):
        self.i.create_refs(*keys)

    def _create_outputs(self, *keys: list[str]):
        self.o.create_refs(*keys)

    def _create_info(self):
        ref_idx_map = {}
        refs = []
        for ref in itertools.chain(self.i.refs.values(), self.o.refs.values()):
            if ref not in ref_idx_map:
                idx = len(ref_idx_map)
                ref_idx_map[ref] = idx
                refs.append(RefInfo(id=f"ref{idx}"))

        node_info = NodeInfo(id=f"node0", title=type(self).__name__)
        for i, (key, ref) in enumerate(self.i.refs.items()):
            ref_info = refs[ref_idx_map[ref]]
            port_info = PortInfo(
                id=f"i{i}",
                text=key,
                kind=PortKind.DST,
                node=node_info,
                ref=ref_info,
            )
            node_info.inputs.append(port_info)
            ref_info.dsts.append(port_info)
        for i, (key, ref) in enumerate(self.o.refs.items()):
            ref_info = refs[ref_idx_map[ref]]
            port_info = PortInfo(
                id=f"o{i}",
                text=key,
                kind=PortKind.SRC,
                node=node_info,
                ref=ref_info,
            )
            node_info.outputs.append(port_info)
            ref_info.srcs.append(port_info)

        return node_info


def simple_atom(outputs: list[str] | None = None):
    """Decorator that converts a function definition to an Atom subclass

    This decorator exists for convenience when an Atom subclass takes no
    constructor arguments and its _evaluate function doesn't use
    **kwargs or need access to self.For more complicated use cases the
    Atom subclass should be declared explicitly. Input Ref names are
    inferred from the decorated function's parameter list.

    Arguments:
        outputs: list[str] | None
            Names of the Atom's output Refs

    """
    if outputs is None:
        outputs = []

    def decorate(func):
        inputs = []
        for name, param in inspect.signature(func).parameters.items():
            if param.kind == inspect.Parameter.POSITIONAL_ONLY:
                raise ValueError(
                    "simple_atom cannot decorate positional only arguments"
                )
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                raise ValueError("simple_atom cannot decorate *args")
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                raise ValueError("simple_atom cannot decorate **kwargs")
            inputs.append(name)

        class Wrapper(Atom):
            def __init__(self):
                super().__init__()
                self._create_inputs(*inputs)
                self._create_outputs(*outputs)

            def _evaluate(self, **kwargs):
                return func(**kwargs)

        Wrapper.__name__ = func.__name__
        Wrapper.__doc__ = func.__doc__
        Wrapper.__module__ = func.__module__
        return Wrapper

    return decorate


class DAG(Node):
    class Passthrough(Atom):
        def _evaluate(self, **kwargs):
            return kwargs

        def _create_paths(self, *keys):
            self._create_inputs(*keys)
            self._create_outputs(*keys)

    def __init__(self):
        self._nodes = {}
        self._input_border = self.Passthrough()
        self._output_border = self.Passthrough()
        self._add_node(self._input_border)
        self._add_node(self._output_border)

    def _add_node(self, node: Node):
        if node in self._nodes:
            raise ValueError("node was already added to DAG")
        # May store a metadata value in the future
        self._nodes[node] = None

    def __call__(self):
        """Evaluate all component nodes respecting dependencies"""
        ref_usage = {}
        for i, node in enumerate(self._nodes):
            for ref in node.o.refs.values():
                if ref not in ref_usage:
                    ref_usage[ref] = ([], [])
                ref_usage[ref][0].append(i)
            for ref in node.i.refs.values():
                if ref not in ref_usage:
                    ref_usage[ref] = ([], [])
                ref_usage[ref][1].append(i)
        edges = []
        for src_nodes, dst_nodes in ref_usage.values():
            edges.extend(itertools.product(src_nodes, dst_nodes))

        sorted_nodes = toposort(list(self._nodes), edges)
        for node in sorted_nodes:
            node()

    def show(self, collapse_refs=True):
        dag_info = self._create_info()
        dot_src = gen_dag_dot(dag_info, collapse_refs=collapse_refs)
        html_src = dot_to_html(dot_src, title=type(self).__name__)
        show_in_webbrowser(html_src.encode())

    @property
    def i(self):
        return self._input_border.i

    @i.setter
    def i(self, refmap):
        self._input_border.i = refmap

    @property
    def o(self):
        return self._output_border.o

    @o.setter
    def o(self, refmap):
        self._output_border.o = refmap

    def _create_inputs(self, *keys: list[str]):
        self._input_border._create_paths(*keys)

    def _create_outputs(self, *keys: list[str]):
        self._output_border._create_paths(*keys)

    def _proxy_inputs(self, arg=None, /, conn=None):
        if conn is None and not isinstance(arg, Node):
            conn = arg
            node = None
        else:
            node = arg

        if node is None:
            node = list(self._nodes)[-1]

        self._input_border.link(node, conn)

    def _proxy_outputs(self, arg=None, /, conn=None):
        if conn is None and not isinstance(arg, Node):
            conn = arg
            node = None
        else:
            node = arg

        if node is None:
            node = list(self._nodes)[-1]

        node.link(self._output_border, conn)

    def _create_info(self):
        dag_info = DAGInfo()
        ref_idx_map = {}
        for node in self._nodes:
            for ref in itertools.chain(node.i.refs.values(), node.o.refs.values()):
                if ref not in ref_idx_map:
                    idx = len(ref_idx_map)
                    ref_idx_map[ref] = idx
                    dag_info.refs.append(RefInfo(id=f"ref{idx}"))

        for i, (node, meta) in enumerate(self._nodes.items()):
            passthrough = isinstance(node, self.Passthrough)
            if node is self._input_border:
                title = "Inputs"
            elif node is self._output_border:
                title = "Outputs"
            else:
                title = type(node).__name__
            node_info = NodeInfo(id=f"node{i}", title=title, passthrough=passthrough)
            dag_info.nodes.append(node_info)
            for j, (key, ref) in enumerate(node.i.refs.items()):
                ref_info = dag_info.refs[ref_idx_map[ref]]
                port_info = PortInfo(
                    id=f"p{j}" if passthrough else f"i{j}",
                    text=key,
                    kind=PortKind.DST,
                    node=node_info,
                    ref=ref_info,
                )
                node_info.inputs.append(port_info)
                ref_info.dsts.append(port_info)
            for j, (key, ref) in enumerate(node.o.refs.items()):
                ref_info = dag_info.refs[ref_idx_map[ref]]
                port_info = PortInfo(
                    id=f"p{j}" if passthrough else f"o{j}",
                    text=key,
                    kind=PortKind.SRC,
                    node=node_info,
                    ref=ref_info,
                )
                node_info.outputs.append(port_info)
                ref_info.srcs.append(port_info)

        return dag_info
