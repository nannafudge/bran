from bran.decorators import schema, field, class_registry


@schema
class MyObject:
    test = field(1)


@schema
class MyObjectNoField:
    test = 1


@schema
class MyObjectConstructed:
    def __init__(self):
        self.test = 1


@schema
class MyObjectCustomFieldName:
    test = field(1, name="test2")


def test_field_decorator():
    test = MyObject()

    assert(class_registry.keys().__contains__(MyObject))
    assert(class_registry[MyObject].keys().__contains__("test"))
    assert(class_registry[MyObject]['test'] == 1)


def test_no_field_decorator():
    test = MyObjectNoField()

    assert (class_registry.keys().__contains__(MyObjectNoField))
    assert (class_registry[MyObjectNoField].keys().__eq__([]))


def test_custom_field_name():
    test = MyObjectCustomFieldName()

    assert(class_registry.keys().__contains__(MyObjectCustomFieldName))
    assert(class_registry[MyObjectCustomFieldName].keys().__contains__("test2"))
    assert(class_registry[MyObjectCustomFieldName]['test2'] == 1)
