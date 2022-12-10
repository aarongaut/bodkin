Bodkin is a Python library to create, evaluate, and visualize computation graphs.

# Usage / terminology

`bodkin.Atom` - a fundamental building block that computes values for its outputs based on its inputs. Atom is what we would conventionally refer to as a node in a graph.

`bodkin.DAG` - a directed acyclic graph that evaluates its nodes in order of dependency.

`bodkin.Node` - a common base class for `Atom` and `DAG`. A DAG consists of Nodes, meaning it can be made of up Atoms and/or other embedded DAGs.


To learn more see the `examples/basic.py` script for basic usage or pass an object into `help()`. Feel free to open an issue for further questions.

# Installation

## From [PyPI](https://pypi.org/project/bodkin/)

Install using pip

```sh
python3 -m pip install bodkin
```

## From source

```sh
python3 -m pip install https://gitlab.com/samflam/bodkin.git
```
