import enum
import struct
from pathlib import Path

from bran.decorators import type_registry, register_type
from bran.exceptions import BranFileException, BranSerializerException
from bran.serializers import Serializer, IntSerializer, StringSerializer, MappingSerializer, ArraySerializer, \
    BoolSerializer, FloatSerializer, SetSerializer
from bran.synchronized import synchronized


class Loader:
    def __init__(self, serializer_registry=None):
        if serializer_registry is None:
            serializer_registry = {
                bool: BoolSerializer,
                int: IntSerializer,
                float: FloatSerializer,
                str: StringSerializer,
                set: SetSerializer,
                dict: MappingSerializer,
                list: ArraySerializer
            }

        self.serializer_registry = serializer_registry
        self._serializer_pool = {}

    def deserialize(self, data, cls=None, **kwargs):
        if kwargs.get("tagging") is True:
            cls_id = struct.unpack('h', data.read(2))[0]

            if not type_registry.__contains__(cls_id):
                raise BranSerializerException(f"Type ID {cls_id} does not exist/is not registered!", cls_id)

            cls = type_registry[cls_id]

        return self.get_serializer(cls).deserialize(self, cls, data, **kwargs)

    def serialize(self, obj, **kwargs):
        cls = type(obj)

        tag = b''
        if kwargs.get("tagging") is True:
            if not type_registry.__contains__(cls):
                raise BranSerializerException(f"Class {str(cls)} is not registered in the type registry!", cls)

            tag = struct.pack('h', type_registry[cls])

        return tag + self.get_serializer(cls).serialize(self, obj, **kwargs)

    def read(self, path: str, cls: type, **kwargs):
        self._validate_path(path)

        with open(path, 'rb') as file:
            return self.deserialize(file, cls, **kwargs)

    def write(self, path: str, obj: object, **kwargs):
        self._validate_path(path)

        with open(path, 'wb') as file:
            file.write(self.serialize(obj, **kwargs))

    def register(self, cls: type, serializer: type):
        self.serializer_registry[cls] = serializer

    def get_serializer(self, cls: type):
        if not self.serializer_registry.__contains__(cls):
            raise BranSerializerException(f"No serializer registered for class {str(cls)}!", cls)

        serializer = self.serializer_registry[cls]
        if not self._serializer_pool.__contains__(serializer):
            self._serializer_pool[serializer] = serializer.__new__(serializer)

        return self._serializer_pool[serializer]

    def _validate_path(self, path):
        if not Path(path).exists():
            raise BranFileException("File path does not exist!", path)
