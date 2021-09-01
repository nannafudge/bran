import builtins
import io
import struct
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bran.decorators import schema, field
from bran.exceptions import BranFileException, BranSerializerException
from bran.loaders import Loader
from bran.serializers import DefaultSerializer


@schema
class MyObject:
    test = field(1)

def test_read_file():
    loader = Loader()
    loader.register(MyObject, DefaultSerializer)

    obj = MyObject()
    serialized = loader.serialize(obj)

    with patch.object(builtins, 'open', return_value=io.BytesIO(serialized)):
        with patch.object(Path, 'exists', return_value=True):
            obj2 = loader.read("", MyObject)

            assert obj.test == obj2.test


def test_read_file_invalid_path():
    loader = Loader()
    loader.register(MyObject, DefaultSerializer)

    with pytest.raises(BranFileException) as exception:
        loader.read("mypath", MyObject)

        assert "mypath" in exception.value

def test_write_file():
    loader = Loader()
    loader.register(MyObject, DefaultSerializer)

    obj = MyObject()
    raw_bytes = io.BytesIO()

    def out(_bytes):
        obj2 = loader.deserialize(io.BytesIO(_bytes), MyObject)
        assert (obj.test == obj2.test)

    with patch.object(raw_bytes, 'write', wraps=out):
        with patch.object(builtins, 'open', return_value=raw_bytes):
            with patch.object(Path, 'exists', return_value=True):
                loader.write("", obj)


def test_write_file_invalid_path():
    loader = Loader()
    loader.register(MyObject, DefaultSerializer)

    with pytest.raises(BranFileException) as exception:
        loader.write("mypath", MyObject())

        assert "mypath" in exception.value

def test_loader_tagged_flag():
    loader = Loader()

    loader.register(MyObject, DefaultSerializer)
    obj = MyObject()

    serialized = loader.serialize(obj, tagging=True)
    obj2 = loader.deserialize(io.BytesIO(serialized), tagging=True)

    assert (type(obj) == type(obj2))
    assert (obj.test == obj2.test)

def test_loader_tagged_unknown_type_tag():
    loader = Loader()

    with pytest.raises(BranSerializerException) as exception:
        loader.deserialize(io.BytesIO(struct.pack('h', 99)), tagging=True)

        assert "99" in exception.value

def test_serialize_unregistered_tagged_type():
    loader = Loader()

    with pytest.raises(BranSerializerException) as exception:
        loader.serialize(MyObject(), tagging=True)

        assert str(MyObject) in exception.value