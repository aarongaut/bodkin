Bodkin is a Python library to create, evaluate, and visualize computation graphs.

# Usage / terminology

`bodkin.Node` - an abstract base class for for a black box that updates its outputs based on its inputs

`bodkin.Atom` - a Node that is a fundamental building block. An Atom provides a function to update its outputs from its inputs. An Atom is what we would conventionally refer to as a node in a graph.

`bodkin.DAG` - a directed acyclic graph that encapsulates a set of Nodes and evaluates them in order of dependency. A DAG consists of Node objects, so it may contain Atoms and/or other embedded DAGs.

Any Node's inputs and outputs may be accessed through its properties `i` and `o`, resepectively. These properties behave like dictionaries but can be linked together so that setting a output on one Node also sets an input on some other Node.

To learn more see the `examples/basic.py` script for a basic usage example or pass an object into `help()`. Feel free to open an issue for further questions.

# Installation

## Dependencies

Basic functionality only relies on the standard library, but visualizing objects via their `show` method requires the `dot` command from [`graphviz`](https://graphviz.org/download/).

## From [PyPI](https://pypi.org/project/bodkin/)

Install using pip

```sh
python3 -m pip install bodkin
```

## From source

```sh
python3 -m pip install https://gitlab.com/samflam/bodkin.git
```
