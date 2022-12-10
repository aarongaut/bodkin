from bodkin import Atom, simple_atom, DAG

# Declaring an Atom class that adds two inputs together


class AddNode1(Atom):
    def __init__(self):
        super().__init__()
        self._create_inputs("x", "y")
        self._create_outputs("z")

    def _evaluate(self, x, y):
        return {"z": x + y}


# Declaring an equivalent class using simple_atom


@simple_atom(outputs=["z"])
def AddNode2(x, y):
    return {"z": x + y}


# Creating instances

nd1 = AddNode1()
nd2 = AddNode2()


# Linking the output of nd1 to an input of nd2

nd1.link(nd2, {"z": "x"})


# Initializing the other input of nd2

nd2.i["y"] = 100


# Initializing the inputs of nd1

nd1.i |= {"x": 1, "y": 10}


# Evaluating the nodes

nd1()
nd2()


# Getting the output

print(nd2.o["z"])  # prints 111


# Declaring a DAG class that has the same internal structure


class TwoAdderNode(DAG):
    def __init__(self):
        super().__init__()
        self._create_inputs("a", "b", "c")
        self._create_outputs("d")

        self.nd1 = AddNode1()
        self._add_node(self.nd1)
        self._proxy_inputs(self.nd1, {"a": "x", "b": "y"})

        self.nd2 = AddNode2()
        self._add_node(self.nd2)
        self._proxy_inputs(self.nd2, {"c": "y"})
        self._proxy_outputs({"z": "d"})

        self.nd1.link(self.nd2, {"z": "x"})


# Creating an instance

two_adder = TwoAdderNode()

# Initializing the DAG's inputs

two_adder.i |= {"a": 1, "b": 10, "c": 100}

# Evaluating the DAG

two_adder()

# Getting the output

print(two_adder.o["d"])  # prints 111

# Show the DAG in your web browser (requires graphviz to be installed)
try:
    two_adder.show()
except CalledProcessError as err:
    print(err)
