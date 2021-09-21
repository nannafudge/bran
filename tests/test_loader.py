import builtins
import io
from pathlib import Path
from unittest.mock import patch

import pytest

from pybran import schema, field

from pybran.exceptions import BranFileException, BranSerializerException
from pybran.loaders import Loader
from pybran.serializers import DefaultSerializer


@schema
class MyObject:
    test = field(1)


class TestLoader:
    def test_read_file(self):
        loader = Loader()
        loader.register(MyObject, DefaultSerializer)

        obj = MyObject()
        serialized = loader.serialize(obj)

        with patch.object(builtins, 'open', return_value=io.BytesIO(serialized)):
            with patch.object(Path, 'is_file', return_value=True):
                obj2 = loader.read("", MyObject)

                assert obj.test == obj2.test

    def test_read_file_invalid_path(self):
        loader = Loader()
        loader.register(MyObject, DefaultSerializer)

        with pytest.raises(BranFileException) as exception:
            loader.read("mypath", MyObject)

            assert "mypath" in exception.value

    def test_write_file(self):
        loader = Loader()
        loader.register(MyObject, DefaultSerializer)

        obj = MyObject()
        raw_bytes = io.BytesIO()

        def out(_bytes):
            obj2 = loader.deserialize(io.BytesIO(_bytes), MyObject)
            assert (obj.test == obj2.test)

        with patch.object(raw_bytes, 'write', wraps=out):
            with patch.object(builtins, 'open', return_value=raw_bytes):
                with patch.object(Path, 'is_file', return_value=True):
                    loader.write("", obj)

    def test_loader_tagged_primitive(self):
        loader = Loader()

        myint = 1
        serialized = loader.serialize(myint, tagging=True)
        myint2 = loader.deserialize(io.BytesIO(serialized), tagging=True)

        assert (type(myint) == type(myint2))
        assert (myint == myint2)

    def test_loader_tagged_flag(self):
        loader = Loader()

        loader.register(MyObject, DefaultSerializer)
        obj = MyObject()

        serialized = loader.serialize(obj, tagging=True)
        obj2 = loader.deserialize(io.BytesIO(serialized), tagging=True)

        assert (type(obj) == type(obj2))
        assert (obj.test == obj2.test)

    def test_loader_tagged_unknown_type_tag(self):
        loader = Loader()

        with pytest.raises(BranSerializerException) as exception:
            loader.deserialize(io.BytesIO(loader.serialize(99)), tagging=True)

            assert "99" in exception.value

    def test_serialize_unregistered_tagged_type(self):
        loader = Loader()

        class NotRegistered:
            test = 1

        with pytest.raises(BranSerializerException) as exception:
            loader.serialize(NotRegistered(), tagging=True)

            assert str(MyObject) in exception.value
