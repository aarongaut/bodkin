import warnings
from abc import ABC, abstractmethod
from collections.abc import Mapping, Iterable, Hashable


class UninitializedRefError(RuntimeError):
    """Raised when getting the value of a Ref before it has been set"""

    pass


class NestedRefWarning(RuntimeWarning):
    pass


class Ref:
    """Reference to a value that can be reassigned"""

    UNINITIALIZED = object()

    def __init__(self):
        self.__value = self.UNINITIALIZED

    def set(self, value):
        self.__value = value
        if isinstance(value, Ref):
            warnings.warn(NestedRefWarning("Storing a Ref inside another Ref"))

    def get(self):
        if self.__value is self.UNINITIALIZED:
            raise UninitializedRefError
        return self.__value

    def reset(self):
        self.__value = self.UNINITIALIZED


class RefMap(Mapping):
    """Dictionary-like object backed by Refs

    Setting and getting items accesses the values contained by Refs,
    not the Refs themselves

    Setting an item without a pre-existing Ref raises a KeyError

    """

    def __init__(self):
        self.refs = {}

    def __getitem__(self, key):
        return self.refs[key].get()

    def __setitem__(self, key, val):
        self.refs[key].set(val)

    def __delitem__(self, key):
        self.refs[key].reset()

    def __contains__(self, key):
        return key in self.refs

    def __len__(self):
        return len(self.refs)

    def __iter__(self):
        return iter(self.refs)

    def __ior__(self, val_map: Mapping, /):
        for key, val in val_map.items():
            self[key] = val
        return self

    def keys(self):
        return self.refs.keys()

    def values(self):
        for ref in self.refs.values():
            yield ref.get()

    def items(self):
        for key, ref in self.refs.items():
            yield key, ref.get()

    def get(self, key, default=None, /):
        """Get the value of a Ref

        If there is no Ref with that key, returns default

        """
        if key not in self:
            return default
        return self[key]

    def set(self, key: str, val, /, *, ignore_missing=False):
        """Get the value of a Ref

        If there is no Ref with that key and ignore_missing is True,
        does nothing.

        """
        if ignore_missing and key not in self:
            return
        self[key] = val

    def set_many(self, val_map: Mapping, /, *, ignore_missing=False):
        """Get the value of multiple Refs

        If there is no Ref with that key and ignore_missing is True,
        does nothing.

        """
        for key, val in val_map.items():
            self.set(key, val, ignore_missing=ignore_missing)

    @staticmethod
    def _resolve_conn(conn: Mapping | Iterable | Hashable) -> dict:
        """Resolve a connection descriptor to a dictionary

        Examples:
            >>> RefMap._resolve_conn({"a": "b", "c": "d"})
            {"a": "b", "c": "d"}

            >>> RefMap._resolve_conn(["a", "b", "c", "d"])
            {"a": "a", "b": "b", "c": "c"}

            >>> RefMap._resolve_conn("abcd")
            {"abcd": "abcd"}

        """
        if isinstance(conn, Mapping):
            return conn
        if isinstance(conn, Iterable) and not isinstance(conn, str):
            return {key: key for key in conn}
        if isinstance(conn, Hashable):
            return {conn: conn}
        raise ValueError(f"Unknown connection type {conn}")

    def link(self, other: "RefMap", /, conn=None):
        """Update another RefMap to share some Refs with self

        Arguments:
            other: RefMap
                The downstream RefMap
            conn:
                A description of the connection. If links and Refs with
                common keys between self and other. Otherwise, uses
                _resolve_conn to get a dictionary mapping self keys to
                other keys.

        """
        self_keys = set(self)
        other_keys = set(other)
        if conn is None:
            conn = {key: key for key in self_keys.intersection(other_keys)}
        else:
            conn = self._resolve_conn(conn)
        for src, dst in conn.items():
            other._replace_ref(dst, self.refs[src])

    def create_refs(self, *keys):
        for key in keys:
            if key in self.refs:
                raise KeyError("Ref already exists")
            self.refs[key] = Ref()

    def _replace_ref(self, key, ref, /):
        if key not in self.refs:
            raise KeyError
        self.refs[key] = ref


class Node(ABC):
    """Base class for all DAG nodes"""

    @abstractmethod
    def __call__(self):
        """Update the Node's outputs based on its inputs"""
        pass

    @abstractmethod
    def show(self, **kwargs):
        """Launch a GUI visualizing the Node"""
        pass

    @property
    @abstractmethod
    def i(self) -> RefMap:
        pass

    @i.setter
    def i(self, refmap: RefMap):
        pass

    @property
    @abstractmethod
    def o(self) -> RefMap:
        pass

    @o.setter
    @abstractmethod
    def o(self, refmap: RefMap):
        pass

    @abstractmethod
    def _create_inputs(self, *keys: list[str]):
        pass

    @abstractmethod
    def _create_outputs(self, *keys: list[str]):
        pass

    def link(self, downstream: "Node", /, conn=None):
        self.o.link(downstream.i, conn)
