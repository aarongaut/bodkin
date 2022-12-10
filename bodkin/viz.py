from dataclasses import dataclass, field
import tempfile
import subprocess
from enum import auto, Enum
import importlib.resources
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer


data_path = importlib.resources.files(__package__) / "data"
STYLE_SRC = (data_path / "style.css").read_text()
SCRIPT_SRC = (data_path / "script.js").read_text()
HTML_TEMPLATE = (data_path / "index.html.template").read_text()


@dataclass
class NodeInfo:
    id: str
    title: str
    passthrough: bool
    inputs: list["PortInfo"] = field(default_factory=list)
    outputs: list["PortInfo"] = field(default_factory=list)

    @property
    def label(self):
        inputs_label = "|".join(f"<{p.id}> {p.text}" for p in self.inputs)
        if self.passthrough:
            return f"-{self.title}-|{inputs_label}"
        outputs_label = "|".join(f"<{p.id}> {p.text}" for p in self.outputs)
        io_label = f"{{{inputs_label}}}|{{{outputs_label}}}"
        return f"-{self.title}-|{{{io_label}}}"


@dataclass
class RefInfo:
    id: str
    srcs: list["PortInfo"] = field(default_factory=list)
    dsts: list["PortInfo"] = field(default_factory=list)


class PortKind(Enum):
    SRC = auto()
    DST = auto()


@dataclass
class DAGInfo:
    nodes: list[NodeInfo] = field(default_factory=list)
    refs: list[RefInfo] = field(default_factory=list)


@dataclass
class PortInfo:
    id: str
    text: str
    kind: PortKind
    node: NodeInfo
    ref: RefInfo

    @property
    def edge_id(self):
        compass = "e" if self.kind == PortKind.SRC else "w"
        return f"{self.node.id}:{self.id}:{compass}"


def gen_node_dot(node: NodeInfo):
    lines = []
    lines.append("digraph G {")
    lines.append("rankdir=LR")
    lines.append("ranksep=2.0")
    lines.append('bgcolor="transparent"')
    lines.append('node [shape=record label="" fontname="monospace" tooltip=" "]')
    lines.append(f'{node.id} [label="{node.label}"]')
    lines.append("}")
    return "\n".join(lines)


def gen_dag_dot(dag: DAGInfo, collapse_refs=True):
    lines = []
    lines.append("digraph G {")
    lines.append("rankdir=LR")
    lines.append("ranksep=2.0")
    lines.append('bgcolor="transparent"')
    lines.append('node [shape=record label="" fontname="monospace" tooltip=" "]')
    lines.append('edge [tooltip=" "]')
    for node in dag.nodes:
        lines.append(f'{node.id} [label="{node.label}"]')

    lines.append("node [shape=point]")

    def edge_id_generator():
        i = 0
        while True:
            yield f"edge{i}"
            i += 1

    gen_id = edge_id_generator()
    for ref in dag.refs:
        attrs = f'class="ref group_{ref.id}"'
        if collapse_refs:
            src_count = len(ref.srcs)
            dst_count = len(ref.dsts)
            if src_count + dst_count <= 1:
                continue
            if src_count == 1 and dst_count == 1:
                src_id = ref.srcs[0].edge_id
                dst_id = ref.dsts[0].edge_id
                # Need to assign an id because after collapsing refs
                # there may be multiple edges between a pair of nodes.
                # In this case graphviz will overwrite earlier edges
                # with later ones unless they have distinct ids.
                full_attrs = f'{attrs} id="{next(gen_id)}" arrowtail=dot dir=both'
                lines.append(f"{src_id} -> {dst_id} [{full_attrs}]")
                continue
        lines.append(f"{ref.id} [{attrs}]")
        for port in ref.srcs:
            full_attrs = f'{attrs} arrowtail=dot dir=both id="{next(gen_id)}"'
            lines.append(f"{port.edge_id} -> {ref.id} [{full_attrs}]")
        for port in ref.dsts:
            lines.append(f'{ref.id} -> {port.edge_id} [{attrs} id="{next(gen_id)}"]')

    lines.append("}")
    return "\n".join(lines)


def dot_to_html(dot_src: str, title: str):
    with tempfile.NamedTemporaryFile(suffix=".dot", mode="w") as dot_file:
        dot_file.write(dot_src)
        dot_file.flush()
        try:
            svg_src = subprocess.run(
                ["dot", "-Tsvg", dot_file.name], check=True, capture_output=True
            ).stdout
        except CalledProcessError as err:
            raise CalledProcessError(err.stderr) from err
    html_src = HTML_TEMPLATE.format(
        title=title,
        style_src=STYLE_SRC,
        svg_src=svg_src.decode(),
        script_src=SCRIPT_SRC,
    )
    return html_src


def show_in_webbrowser(data: bytes):
    class ServeDataHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response_only(200)
            self.end_headers()
            self.wfile.write(data)

    server = HTTPServer(("localhost", 0), ServeDataHandler)
    url = f"http://localhost:{server.server_address[1]}"
    webbrowser.open(url)
    server.handle_request()
    server.server_close()
