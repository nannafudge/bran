from io import BufferedReader, RawIOBase
from unittest.mock import MagicMock, patch

from bran.loaders import Loader
from bran.serializers import Serializer
from tests.test_decorators import MyObject


class MyObject:
    test = 1


Serializer.serialize = MagicMock(return_value={})
Serializer.deserialize = MagicMock(return_value=MyObject())

serializers = {
    MyObject: Serializer()
}

file = BufferedReader(raw=RawIOBase())
file.read = MagicMock(return_value="{}")


def test_serialize():
    loader = Loader()

    obj = MyObject()

    result = loader.serialize(obj=obj)
    Serializer.serialize.assert_called_once_with(loader=loader, obj=obj)

def test_deserialize():
    loader = Loader(serializers)

    result = loader.deserialize(cls=MyObject, data={})
    Serializer.deserialize.assert_called_once()

def test_read_file():
    loader = Loader(serializers)

    with patch.object(open, '', return_value=file):
        loader.read("", )


def test_read_file_raw():
    loader = Loader(serializers)

    loader.read("resources/test")

def test_write_file():
    pass
