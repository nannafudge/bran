import pytest

from bran.decorators import schema, field, class_registry, type_registry, name_registry, register_class
from bran.exceptions import BranRegistrationException


@schema
class MyObject:
    test = field(1)


@schema
class MyObjectNoField:
    test2 = 2


@schema
class NestedObject:
    test3 = field(MyObject())


def test_field_decorator():
    assert class_registry.keys().__contains__(MyObject)
    assert class_registry[MyObject].keys().__contains__("test")
    assert class_registry[MyObject]["test"] == int

    assert type_registry[type_registry[int]] == int
    assert name_registry[MyObject]["test"] == 1
    assert name_registry[MyObject][1] == "test"

    assert MyObject().test == 1


def test_no_field_decorator():
    assert class_registry.keys().__contains__(MyObjectNoField)
    assert not class_registry[MyObjectNoField]

    assert name_registry.__contains__(MyObjectNoField)
    assert not name_registry[MyObjectNoField]


def test_manually_register_field():
    assert class_registry.keys().__contains__(MyObjectNoField)
    assert not class_registry[MyObjectNoField]

    assert name_registry.__contains__(MyObjectNoField)
    assert not name_registry[MyObjectNoField]

    register_class(MyObjectNoField, {"test2": int})

    assert class_registry.keys().__contains__(MyObject)
    assert class_registry[MyObjectNoField].keys().__contains__("test2")
    assert class_registry[MyObjectNoField]["test2"] == int

    assert type_registry[type_registry[int]] == int
    assert name_registry[MyObjectNoField]["test2"] == 1
    assert name_registry[MyObjectNoField][1] == "test2"

    assert MyObjectNoField().test2 == 2


def test_register_nested_object():
    assert class_registry.keys().__contains__(NestedObject)
    assert class_registry[NestedObject]["test3"] == MyObject

    assert type_registry[type_registry[MyObject]] == MyObject
    assert name_registry[NestedObject]["test3"] == 1
    assert name_registry[NestedObject][1] == "test3"

    assert isinstance(NestedObject().test3, MyObject)


def test_add_existing_type():
    register_class(MyObject, {"test": int })
    assert type_registry[int] == 2

    register_class(MyObjectNoField, {"test2": int})
    assert type_registry[int] == 2