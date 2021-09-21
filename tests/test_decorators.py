import pytest

from pybran.decorators import schema, field, class_registry, type_registry, name_registry, register_class
from pybran.exceptions import BranRegistrationException


@schema
class MyObject:
    test = field(1)


@schema
class MyObjectNoField:
    test2 = 2


@schema
class NestedObject:
    test3 = field(MyObject())


@schema
class NestedObjectOnlyType:
    test = field(int)
    nested = field(MyObject)


class ComplexClass:
    test = [1, 2, 3]
    test2 = {}


class NestedComplexClass:
    nested = ComplexClass()
    test = 1


class TestDecorators:
    def test_field_decorator(self):
        assert class_registry.contains(MyObject)
        assert class_registry.get(MyObject).contains("test")
        assert class_registry.get(MyObject).get("test") == int

        assert type_registry.get(type_registry.get(int)) == int
        assert name_registry.get(MyObject).get("test") == 1
        assert name_registry.get(MyObject).get(1) == "test"

        assert MyObject().test == 1

    def test_no_field_decorator(self):
        assert class_registry.contains(MyObjectNoField)
        assert not class_registry.get(MyObjectNoField)

        assert name_registry.contains(MyObjectNoField)
        assert not name_registry.get(MyObjectNoField)

    def test_manually_register_class(self):
        assert class_registry.contains(MyObjectNoField)
        assert not class_registry.get(MyObjectNoField)

        assert name_registry.contains(MyObjectNoField)
        assert not name_registry.get(MyObjectNoField)

        register_class(MyObjectNoField, {"test2": int})

        assert class_registry.contains(MyObjectNoField)
        assert class_registry.get(MyObjectNoField).get("test2") == int

        assert type_registry.get(type_registry.get(int)) == int
        assert name_registry.get(MyObjectNoField).get("test2") == 1
        assert name_registry.get(MyObjectNoField).get(1) == "test2"

        assert MyObjectNoField().test2 == 2

    def test_manually_register_complex_class(self):
        register_class(NestedComplexClass, {"nested": NestedComplexClass.nested, "test": NestedComplexClass.test})
        register_class(ComplexClass, {"test": ComplexClass.test, "test2": ComplexClass.test2})

        assert class_registry.contains(NestedComplexClass)
        assert class_registry.contains(ComplexClass)

        assert class_registry.get(NestedComplexClass).get("test") == int
        assert class_registry.get(NestedComplexClass).get("nested") == ComplexClass

        assert class_registry.get(ComplexClass).get("test") == list
        assert class_registry.get(ComplexClass).get("test2") == dict

        assert type_registry.get(type_registry.get(NestedComplexClass)) == NestedComplexClass
        assert type_registry.get(type_registry.get(ComplexClass)) == ComplexClass

        assert name_registry.get(ComplexClass).get("test") == 1
        assert name_registry.get(NestedComplexClass).get("nested") == 1

    def test_register_nested_object(self):
        assert class_registry.contains(NestedObject)
        assert class_registry.get(NestedObject).get("test3") == MyObject

        assert type_registry.get(type_registry.get(MyObject)) == MyObject
        assert name_registry.get(NestedObject).get("test3") == 1
        assert name_registry.get(NestedObject).get(1) == "test3"

        assert isinstance(NestedObject().test3, MyObject)

    def test_register_object_only_type_info(self):
        assert class_registry.contains(NestedObjectOnlyType)

        assert class_registry.get(NestedObjectOnlyType).get("test") == int
        assert class_registry.get(NestedObjectOnlyType).get("nested") == MyObject

        assert name_registry.get(NestedObjectOnlyType).get("test") == 1
        assert name_registry.get(NestedObjectOnlyType).get(1) == "test"
        assert name_registry.get(NestedObjectOnlyType).get("nested") == 2
        assert name_registry.get(NestedObjectOnlyType).get(2) == "nested"

    def test_add_existing_type(self):
        register_class(MyObject, {"test": int})
        assert type_registry.get(int) == 2

        register_class(MyObjectNoField, {"test2": int})
        assert type_registry.get(int) == 2

    def test_get_unregistered_type_no_autoregister(self):
        class UnregisteredClass:
            pass

        with pytest.raises(BranRegistrationException):
            type_registry.get(UnregisteredClass)
