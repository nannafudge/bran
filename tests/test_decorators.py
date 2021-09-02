from pybran.decorators import schema, field, class_registry, type_registry, name_registry, register_class


@schema
class MyObject:
    test = field(1)


@schema
class MyObjectNoField:
    test2 = 2


@schema
class NestedObject:
    test3 = field(MyObject())


class ComplexClass:
    test = [1, 2, 3]
    test2 = {}


class NestedComplexClass:
    nested = ComplexClass()
    test = 1


class TestDecorators:
    def test_field_decorator(self):
        assert class_registry.keys().__contains__(MyObject)
        assert class_registry[MyObject].keys().__contains__("test")
        assert class_registry[MyObject]["test"] == int

        assert type_registry[type_registry[int]] == int
        assert name_registry[MyObject]["test"] == 1
        assert name_registry[MyObject][1] == "test"

        assert MyObject().test == 1

    def test_no_field_decorator(self):
        assert class_registry.keys().__contains__(MyObjectNoField)
        assert not class_registry[MyObjectNoField]

        assert name_registry.__contains__(MyObjectNoField)
        assert not name_registry[MyObjectNoField]

    def test_manually_register_class(self):
        assert class_registry.keys().__contains__(MyObjectNoField)
        assert not class_registry[MyObjectNoField]

        assert name_registry.__contains__(MyObjectNoField)
        assert not name_registry[MyObjectNoField]

        register_class(MyObjectNoField, {"test2": int})

        assert class_registry.keys().__contains__(MyObjectNoField)
        assert class_registry[MyObjectNoField]["test2"] == int

        assert type_registry[type_registry[int]] == int
        assert name_registry[MyObjectNoField]["test2"] == 1
        assert name_registry[MyObjectNoField][1] == "test2"

        assert MyObjectNoField().test2 == 2

    def test_manually_register_complex_class(self):
        register_class(NestedComplexClass, {"nested": NestedComplexClass.nested, "test": NestedComplexClass.test})
        register_class(ComplexClass, {"test": ComplexClass.test, "test2": ComplexClass.test2})

        assert class_registry.keys().__contains__(NestedComplexClass)
        assert class_registry.keys().__contains__(ComplexClass)

        assert class_registry[NestedComplexClass]["test"] == int
        assert class_registry[NestedComplexClass]["nested"] == ComplexClass

        assert class_registry[ComplexClass]["test"] == list
        assert class_registry[ComplexClass]["test2"] == dict

        assert type_registry[type_registry[NestedComplexClass]] == NestedComplexClass
        assert type_registry[type_registry[ComplexClass]] == ComplexClass

        assert name_registry[ComplexClass]["test"] == 1
        assert name_registry[NestedComplexClass]["nested"] == 1

    def test_register_nested_object(self):
        assert class_registry.keys().__contains__(NestedObject)
        assert class_registry[NestedObject]["test3"] == MyObject

        assert type_registry[type_registry[MyObject]] == MyObject
        assert name_registry[NestedObject]["test3"] == 1
        assert name_registry[NestedObject][1] == "test3"

        assert isinstance(NestedObject().test3, MyObject)

    def test_add_existing_type(self):
        register_class(MyObject, {"test": int})
        assert type_registry[int] == 2

        register_class(MyObjectNoField, {"test2": int})
        assert type_registry[int] == 2
