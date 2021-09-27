import pytest

from pybran import schema, field, register_class, refresh, type_registry, class_registry, register_alias

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


@schema
class ClassCustomAliases:
    test = field(int, alias=b'\x05')
    test2 = field(int)


@schema
class InheritFields(ClassCustomAliases):
    pass


class ComplexClass:
    test = [1, 2, 3]
    test2 = {}


class NestedComplexClass:
    nested = ComplexClass()
    test = 1


class TestDecorators:
    def test_registry_refresh(self):
        type_registry_mapping = type_registry.registry.copy()
        class_registry_mapping = class_registry.registry.copy()

        refresh()

        assert len(type_registry.items()) == len(type_registry_mapping.items())
        assert len(class_registry.items()) == len(class_registry_mapping.items())

    def test_field_decorator(self):
        class_definition = class_registry.get(MyObject)

        assert class_definition.fields.contains("test")
        assert class_definition.fields.get("test") == int

        assert type_registry.get(type_registry.get(int)) == int

        assert class_definition.aliases.get("test") == 1
        assert class_definition.aliases.get(1) == "test"

        assert MyObject().test == 1

    def test_no_field_decorator(self):
        class_definition = class_registry.get(MyObjectNoField)

        assert len(class_definition.fields) == 0
        assert len(class_definition.aliases) == 0

    def test_manually_register_class(self):
        class_definition = class_registry.get(MyObjectNoField)

        assert len(class_definition.fields) == 0
        assert len(class_definition.aliases) == 0

        register_class(MyObjectNoField, {"test2": int})

        class_definition_updated = class_registry.get(MyObjectNoField)

        assert class_definition_updated.fields.get("test2") == int
        assert type_registry.get(type_registry.get(int)) == int

        assert class_definition_updated.aliases.get("test2") == 1
        assert class_definition_updated.aliases.get(1) == "test2"

        assert MyObjectNoField().test2 == 2

    def test_manually_register_complex_class(self):
        register_class(NestedComplexClass, {"nested": NestedComplexClass.nested, "test": NestedComplexClass.test})
        register_class(ComplexClass, {"test": ComplexClass.test, "test2": ComplexClass.test2})

        nested_class_definition = class_registry.get(NestedComplexClass)
        complex_class_definition = class_registry.get(ComplexClass)

        assert nested_class_definition.fields.get("test") == int
        assert nested_class_definition.fields.get("nested") == ComplexClass

        assert complex_class_definition.fields.get("test") == list
        assert complex_class_definition.fields.get("test2") == dict

        assert type_registry.get(type_registry.get(NestedComplexClass)) == NestedComplexClass
        assert type_registry.get(type_registry.get(ComplexClass)) == ComplexClass

        assert nested_class_definition.aliases.get("nested") == 1
        assert complex_class_definition.aliases.get("test") == 1

    def test_register_nested_object(self):
        class_definition = class_registry.get(NestedObject)
        assert class_definition.fields.get("test3") == MyObject

        assert type_registry.get(type_registry.get(MyObject)) == MyObject

        assert class_definition.aliases.get("test3") == 1
        assert class_definition.aliases.get(1) == "test3"

        assert isinstance(NestedObject().test3, MyObject)

    def test_register_object_only_type_info(self):
        class_definition = class_registry.get(NestedObjectOnlyType)

        assert class_definition.fields.get("test") == int
        assert class_definition.fields.get("nested") == MyObject

        assert class_definition.aliases.get("test") == 1
        assert class_definition.aliases.get(1) == "test"
        assert class_definition.aliases.get("nested") == 2
        assert class_definition.aliases.get(2) == "nested"

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

    def test_registry_remove(self):
        class TestRegistryRemove:
            pass

        type_registry.add(TestRegistryRemove)
        assert type_registry.contains(TestRegistryRemove)

        registered_id = type_registry.get(TestRegistryRemove)
        popped_id = type_registry.remove(TestRegistryRemove)
        assert popped_id == registered_id

        assert not type_registry.contains(TestRegistryRemove)

    def test_custom_alias(self):
        class_definition = class_registry.get(ClassCustomAliases)

        assert class_definition.fields.get("test") == int

        assert class_definition.aliases.get("test") == b'\x05'
        assert class_definition.aliases.get(b'\x05') == "test"

        assert class_definition.aliases.get("test2") == 1
        assert class_definition.aliases.get(1) == "test2"

    def test_inherit_fields(self):
        class_definition = class_registry.get(InheritFields)

        assert class_definition.fields.get("test") == int

        assert class_definition.aliases.get("test") == b'\x05'
        assert class_definition.aliases.get(b'\x05') == "test"

        assert class_definition.aliases.get("test2") == 1
        assert class_definition.aliases.get(1) == "test2"

    def test_ignore_fields(self):
        class InheritIgnoreField(ClassCustomAliases):
            pass

        register_class(InheritIgnoreField, ignore=["test2"])

        class_definition = class_registry.get(InheritIgnoreField)

        assert class_definition.fields.get("test") == int
        assert class_definition.aliases.get("test") == b'\x05'
        assert class_definition.aliases.get(b'\x05') == "test"

        assert not class_definition.fields.contains("test2")
        assert not class_definition.aliases.contains("test2")

    def test_custom_alias_register(self):
        class_definition = class_registry.get(ClassCustomAliases)

        class_definition.aliases.clear()

        register_alias(ClassCustomAliases, "test", "newalias")

        assert class_definition.fields.get("test") == int

        assert class_definition.aliases.get("test") == "newalias"
        assert class_definition.aliases.get("newalias") == "test"