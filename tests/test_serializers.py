import io

import pytest

from bran.decorators import schema, field
from bran.exceptions import BranSerializerException
from bran.loaders import Loader
from bran.serializers import DefaultSerializer


@schema
class SimpleObject:
    test = field(1)
    test2 = field("Hello, World!")
    test3 = field(True)
    test4 = field(2.1)

    mapping = field({"test": "mapping", 1: 2, 3: False, True: 4})
    collection = field(["test", 1, True, {"nested": "mapping", 2: 3}])
    set = field({"my", "set"})


@schema
class NestedObject:
    test = field(SimpleObject())

class ObjectNoFields:
    pass


def test_bool_serializer():
    mybool = True

    loader = Loader()

    serialized = loader.serialize(mybool)

    mybool2 = loader.deserialize(io.BytesIO(serialized), bool)

    assert (isinstance(mybool2, bool))
    assert (mybool == mybool2)


def test_int_serializer():
    myint = 1

    loader = Loader()

    serialized = loader.serialize(myint)

    myint2 = loader.deserialize(io.BytesIO(serialized), int)

    assert (isinstance(myint2, int))
    assert (myint == myint2)

def test_float_serializer():
    myfloat = 2.1

    loader = Loader()

    serialized = loader.serialize(myfloat)

    myfloat2 = loader.deserialize(io.BytesIO(serialized), float)

    assert (isinstance(myfloat2, float))
    assert (myfloat == myfloat2)

def test_string_serializer():
    mystring = "Hello, World!"

    loader = Loader()

    serialized = loader.serialize(mystring)

    mystring2 = loader.deserialize(io.BytesIO(serialized), str)

    assert (isinstance(mystring2, str))
    assert (mystring == mystring2)


def test_set_serializer():
    myset = {"a", "b", "c"}

    loader = Loader()

    serialized = loader.serialize(myset)

    myset2 = loader.deserialize(io.BytesIO(serialized), set)

    assert (isinstance(myset2, set))
    assert (myset == myset2)


def test_dict_serializer():
    mydict = {"a": "b", 1: 2, 2: True, "3": 4}

    loader = Loader()

    serialized = loader.serialize(mydict)

    mydict2 = loader.deserialize(io.BytesIO(serialized), dict)

    assert (isinstance(mydict2, dict))
    assert (mydict == mydict2)


def test_list_serializer():
    mylist = ["a", 1, True, 2.5, {"a": 1}, {"test": "set"}, [1, 2, 3, 4]]

    loader = Loader()

    serialized = loader.serialize(mylist)

    mylist2 = loader.deserialize(io.BytesIO(serialized), list)

    assert (isinstance(mylist2, list))
    assert (mylist == mylist2)


def test_default_serializer():
    obj = SimpleObject()
    loader = Loader()

    loader.register(SimpleObject, DefaultSerializer)

    serialized = loader.serialize(obj)

    obj2 = loader.deserialize(io.BytesIO(serialized), SimpleObject)
    assert (isinstance(obj2, SimpleObject))

    assert (obj.test == obj2.test)
    assert (obj.test2 == obj2.test2)
    assert (obj.test3 == obj2.test3)
    assert (obj.test4 == obj2.test4)
    assert (obj.mapping == obj2.mapping)
    assert (obj.collection == obj2.collection)
    assert (obj.set == obj2.set)
    assert (len(obj2.__dict__.keys()) == 7)


def test_default_serializer_nested_object():
    obj = NestedObject()
    loader = Loader()

    loader.register(SimpleObject, DefaultSerializer)
    loader.register(NestedObject, DefaultSerializer)

    serialized = loader.serialize(obj)

    obj2 = loader.deserialize(io.BytesIO(serialized), NestedObject)

    assert isinstance(obj2, NestedObject)
    assert isinstance(obj2.test, SimpleObject)
    assert obj2.test.test == obj.test.test
    assert obj2.test.test2 == obj.test.test2
    assert obj2.test.test3 == obj.test.test3
    assert obj2.test.test4 == obj.test.test4
    assert obj2.test.mapping == obj.test.mapping
    assert obj2.test.collection == obj.test.collection
    assert obj2.test.set == obj.test.set


def test_no_serializer_defined():
    loader = Loader()

    with pytest.raises(BranSerializerException) as exception:
        loader.serialize(SimpleObject())

        assert str(SimpleObject) in exception.value


def test_serialize_unregistered_type_with_tagging():
    loader = Loader()

    with pytest.raises(BranSerializerException) as exception:
        DefaultSerializer().serialize(loader, ObjectNoFields(), tagging=True)

        assert str(ObjectNoFields) in exception.value