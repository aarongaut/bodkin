import pytest

from bodkin import UninitializedRefError, NestedRefWarning, RefMap


def test_getset():
    refmap = RefMap()
    refmap.create_refs("foo")
    refmap["foo"] = "bar"
    assert refmap["foo"] == "bar"


def test_uninitialized():
    refmap = RefMap()
    refmap.create_refs("foo")
    with pytest.raises(UninitializedRefError):
        refmap["foo"]


def test_del():
    refmap = RefMap()
    refmap.create_refs("foo")
    refmap["foo"] = "bar"
    del refmap["foo"]
    with pytest.raises(UninitializedRefError):
        refmap["foo"]


def test_no_ref_get():
    refmap = RefMap()
    with pytest.raises(KeyError):
        refmap["foo"]


def test_no_ref_set():
    refmap = RefMap()
    with pytest.raises(KeyError):
        refmap["foo"] = 5


def test_no_ref_del():
    refmap = RefMap()
    with pytest.raises(KeyError):
        del refmap["foo"]


def test_iter():
    refmap = RefMap()
    refmap.create_refs("foo")
    assert list(refmap) == ["foo"]


def test_keys():
    refmap = RefMap()
    refmap.create_refs("foo")
    assert list(refmap.keys()) == ["foo"]


def test_values():
    refmap = RefMap()
    refmap.create_refs("foo")
    refmap["foo"] = "bar"
    assert list(refmap.values()) == ["bar"]


def test_values():
    refmap = RefMap()
    refmap.create_refs("foo")
    refmap["foo"] = "bar"
    assert list(refmap.items()) == [("foo", "bar")]


def test_get_missing():
    refmap = RefMap()
    assert refmap.get("foo") is None


def test_get_missing_default():
    refmap = RefMap()
    assert refmap.get("foo", "bar") == "bar"


def test_set_missing():
    refmap = RefMap()
    with pytest.raises(KeyError):
        refmap.set("foo", "bar")


def test_set_missing():
    refmap = RefMap()
    refmap.set("foo", "bar", ignore_missing=True)
    assert list(refmap.values()) == []


def test_set_many():
    refmap = RefMap()
    refmap.create_refs("foo")
    refmap.set_many({"foo": "bar", "baz": "qux"}, ignore_missing=True)
    assert list(refmap.items()) == [("foo", "bar")]


def test_ior():
    refmap = RefMap()
    refmap.create_refs("foo", "bar")
    refmap |= {"foo": 5, "bar": 10}
    assert dict(refmap) == {"foo": 5, "bar": 10}


def test_link():
    upstream = RefMap()
    upstream.create_refs("foo", "bar", "baz", "qux")
    downstream = RefMap()
    downstream.create_refs("foo", "bar", "baz2", "qux2")
    downstream |= {"foo": None, "bar": None, "baz2": None, "qux2": None}

    upstream.link(downstream)
    upstream |= {"foo": 1, "bar": 2, "baz": 3, "qux": 4}

    assert dict(downstream) == {"foo": 1, "bar": 2, "baz2": None, "qux2": None}


def test_link_explicit():
    upstream = RefMap()
    upstream.create_refs("foo", "bar", "baz", "qux")
    downstream = RefMap()
    downstream.create_refs("foo2", "bar2", "baz2", "qux2")
    downstream |= {"foo2": None, "bar2": None, "baz2": None, "qux2": None}

    upstream.link(downstream, {"foo": "foo2", "bar": "bar2"})
    upstream |= {"foo": 1, "bar": 2, "baz": 3, "qux": 4}

    assert dict(downstream) == {"foo2": 1, "bar2": 2, "baz2": None, "qux2": None}


def test_link_list():
    upstream = RefMap()
    upstream.create_refs("foo", "bar", "baz", "qux")
    downstream = RefMap()
    downstream.create_refs("foo", "bar", "baz", "qux")
    downstream |= {"foo": None, "bar": None, "baz": None, "qux": None}

    upstream.link(downstream, ["foo", "baz"])
    upstream |= {"foo": 1, "bar": 2, "baz": 3, "qux": 4}

    assert dict(downstream) == {"foo": 1, "bar": None, "baz": 3, "qux": None}


def test_link_key():
    upstream = RefMap()
    upstream.create_refs("foo", "bar", "baz", "qux")
    downstream = RefMap()
    downstream.create_refs("foo", "bar", "baz", "qux")
    downstream |= {"foo": None, "bar": None, "baz": None, "qux": None}

    upstream.link(downstream, "foo")
    upstream |= {"foo": 1, "bar": 2, "baz": 3, "qux": 4}
    assert dict(downstream) == {"foo": 1, "bar": None, "baz": None, "qux": None}


def test_link_explicit_missing():
    upstream = RefMap()
    upstream.create_refs("foo")
    downstream = RefMap()
    downstream.create_refs("bar")
    with pytest.raises(KeyError):
        upstream.link(downstream, {"foo": "foo"})
    with pytest.raises(KeyError):
        upstream.link(downstream, {"bar": "bar"})


def test_link_list_missing():
    upstream = RefMap()
    upstream.create_refs("foo")
    downstream = RefMap()
    downstream.create_refs("bar")
    with pytest.raises(KeyError):
        upstream.link(downstream, ["foo"])
    with pytest.raises(KeyError):
        upstream.link(downstream, ["bar"])


def test_link_key_missing():
    upstream = RefMap()
    upstream.create_refs("foo")
    downstream = RefMap()
    downstream.create_refs("bar")
    with pytest.raises(KeyError):
        upstream.link(downstream, "foo")
    with pytest.raises(KeyError):
        upstream.link(downstream, "bar")
