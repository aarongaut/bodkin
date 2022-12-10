import pytest

from bodkin import Ref, UninitializedRefError, NestedRefWarning


def test_getset():
    ref = Ref()
    ref.set("qwer")
    assert ref.get() == "qwer"


def test_uninitialized():
    ref = Ref()
    with pytest.raises(UninitializedRefError):
        ref.get()


def test_reset():
    ref = Ref()
    ref.set("qwer")
    ref.reset()
    with pytest.raises(UninitializedRefError):
        ref.get()


def test_nested_ref():
    ref = Ref()
    ref2 = Ref()
    with pytest.warns(NestedRefWarning):
        ref.set(ref2)
