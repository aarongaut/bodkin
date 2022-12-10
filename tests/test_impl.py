import pytest

from bodkin import (
    Ref,
    Atom,
    simple_atom,
    DAG,
    toposort,
    CycleError,
    UninitializedRefError,
)


@simple_atom(outputs=["z"])
def AdderNode(x, y):
    return {"z": x + y}


@simple_atom(outputs=["z"])
def MultNode(x, y):
    return {"z": x * y}


class AddMultDAG(DAG):
    def __init__(self):
        super().__init__()
        self._create_inputs("term1", "term2", "factor")
        self._create_outputs("result")

        adder = AdderNode()
        self._add_node(adder)
        self._proxy_inputs({"term1": "x", "term2": "y"})

        mult = MultNode()
        self._add_node(mult)
        self._proxy_inputs({"factor": "y"})
        self._proxy_outputs({"z": "result"})
        adder.link(mult, {"z": "x"})


@simple_atom(outputs=["x"])
def EchoNode(x):
    return {"x": x}


class WrapperDAG(DAG):
    def __init__(self, node):
        super().__init__()
        self._add_node(node)
        self._create_inputs(*node.i)
        self._create_outputs(*node.o)
        self._proxy_inputs()
        self._proxy_outputs()


def test_adder():
    adder = AdderNode()
    adder.i |= {"x": 10, "y": 20}
    adder()
    assert adder.o["z"] == 30


def test_uninitialized():
    adder = AdderNode()
    adder.i |= {"x": 10}
    with pytest.raises(UninitializedRefError):
        adder()


def test_link():
    adder = AdderNode()
    mult = MultNode()

    adder.i |= {"x": 10, "y": 20}
    adder.link(mult, {"z": "x"})
    mult.i["y"] = 10

    adder()
    mult()
    assert mult.o["z"] == 300


def test_dag():
    dag = AddMultDAG()
    dag.i |= {"term1": 10, "term2": 20, "factor": 10}
    dag()
    assert dag.o["result"] == 300


def test_link_dags():
    dag1 = AddMultDAG()
    dag1.i |= {"term1": 10, "term2": 20, "factor": 10}
    dag2 = AddMultDAG()
    dag2.i |= {"term2": 20, "factor": 10}
    dag1.link(dag2, {"result": "term1"})
    dag1()
    dag2()
    assert dag2.o["result"] == 3200


def test_nested_link():
    echo1 = EchoNode()
    echo2 = EchoNode()
    for i in range(5):
        echo1 = WrapperDAG(echo1)
        echo2 = WrapperDAG(echo2)
    echo1.link(echo2)
    echo1.i["x"] = "foo"
    echo1()
    echo2()
    assert echo2.o["x"] == "foo"


def comes_before(values, first, second):
    return values.index(first) < values.index(second)


def test_toposort():
    assert set(toposort(["a", "b", "c"], [])) == set(["a", "b", "c"])

    assert toposort(["a", "b", "c"], [(2, 1), (1, 0)]) == ["c", "b", "a"]

    result = toposort(["a", "b", "c"], [(2, 1)])
    assert comes_before(result, "c", "b")

    result = toposort(["a", "b", "c", "d"], [(0, 1), (0, 2), (1, 3), (2, 3)])
    assert comes_before(result, "a", "b")
    assert comes_before(result, "a", "c")
    assert comes_before(result, "b", "d")
    assert comes_before(result, "c", "d")

    result = toposort(["d", "c", "b", "a"], [(3, 2), (3, 1), (2, 0), (1, 0)])
    assert comes_before(result, "a", "b")
    assert comes_before(result, "a", "c")
    assert comes_before(result, "b", "d")
    assert comes_before(result, "c", "d")

    with pytest.raises(CycleError):
        toposort(["a"], [(0, 0)])

    with pytest.raises(CycleError):
        toposort(["a", "b"], [(0, 1), (1, 0)])

    with pytest.raises(CycleError):
        toposort(["a", "b", "c"], [(0, 1), (1, 2), (2, 0)])
