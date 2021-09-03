"""
Module for Base Bran serializers
"""
import struct

from pybran.decorators import class_registry, type_registry, name_registry
from pybran.exceptions import BranSerializerException


class Serializer:
    """
    Base Serializer class
    """
    def serialize(self, loader, obj, **kwargs):
        """
        Attempt to serialize a type/object

        :param loader: The loader that invoked the method
        :param obj: The object to serialize
        :param **kwargs: Additional arguments to be passed to serialize

        :rtype: Serialized version of :obj:
        """

    def deserialize(self, loader, cls, data, **kwargs):
        """
        Attempt to deserialize a type/object

        :param loader: The loader that invoked the method
        :param cls: The type to deserialize to
        :param data: Data to deserialize from
        :param **kwargs: Additional arguments to be passed to deserialize

        :rtype: Instance of :cls: deserialized from :input:
        """


class DefaultSerializer(Serializer):
    """
    Default class serializer
    """
    def serialize(self, loader, obj, **kwargs):
        fields = class_registry.get(type(obj), None)

        if fields is None:
            raise BranSerializerException("No fields registered for type", obj)

        buffer = b''
        for name in fields.keys():
            buffer += loader.serialize(name_registry.get(type(obj)).get(name), **kwargs)
            buffer += loader.serialize(getattr(obj, name), **kwargs)

        return buffer

    def deserialize(self, loader, cls, data, **kwargs):
        obj = cls.__new__(cls)

        size = len(data.getbuffer())

        while size - data.tell() >= 4:
            name = name_registry.get(cls).get(loader.deserialize(data, int, **kwargs))
            val = loader.deserialize(data, class_registry.get(cls).get(name), **kwargs)

            setattr(obj, name, val)

        return obj


class BoolSerializer(Serializer):
    """
    Boolean serializer that serializes to binary
    """
    def serialize(self, loader, obj, **kwargs):
        return struct.pack('?', obj)

    def deserialize(self, loader, cls, data, **kwargs):
        return struct.unpack('?', data.read(1))[0]


class IntSerializer(Serializer):
    """
    Int serializer that serializes to binary
    """
    def serialize(self, loader, obj, **kwargs):
        return struct.pack('i', obj)

    def deserialize(self, loader, cls, data, **kwargs):
        return struct.unpack('i', data.read(4))[0]


class FloatSerializer(Serializer):
    """
    Float serializer that serializes to binary
    """
    def serialize(self, loader, obj, **kwargs):
        return struct.pack('d', obj)

    def deserialize(self, loader, cls, data, **kwargs):
        return struct.unpack('d', data.read(8))[0]


class StringSerializer(Serializer):
    """
    String serializer that serializes to binary
    """
    def serialize(self, loader, obj, **kwargs):
        return struct.pack('h', len(obj)) + bytes(obj, "UTF-8")

    def deserialize(self, loader, cls, data, **kwargs):
        length = struct.unpack('h', data.read(2))[0]

        return data.read(length).decode("UTF-8")


class SetSerializer(Serializer):
    """
    Set serializer that serializes to binary
    """
    def serialize(self, loader, obj, **kwargs):
        buffer = b''
        buffer += struct.pack('h', len(obj))

        for item in obj:
            buffer += struct.pack('h', type_registry.get(type(item), autoregister=True))
            buffer += loader.serialize(item, **kwargs)

        return buffer

    def deserialize(self, loader, cls, data, **kwargs):
        _set = set()

        length = struct.unpack('h', data.read(2))[0]

        for i in range(0, length):
            item_type = struct.unpack('h', data.read(2))[0]
            _set.add(loader.deserialize(data, type_registry.get(item_type), **kwargs))

        return _set


# TODO: Optimise for maps where k,v pairs are strictly typed, so will only need to write one key_id, val_id for entire map
class MappingSerializer(Serializer):
    """
    Mapping serializer that serializes to binary
    """
    def serialize(self, loader, obj, **kwargs):
        buffer = b''
        buffer += struct.pack('h', len(obj))

        for key, value in obj.items():
            buffer += struct.pack('h', type_registry.get(type(key), autoregister=True))
            buffer += loader.serialize(key, **kwargs)

            buffer += struct.pack('h', type_registry.get(type(value), autoregister=True))
            buffer += loader.serialize(value, **kwargs)

        return buffer

    def deserialize(self, loader, cls, data, **kwargs):
        obj = {}

        length = struct.unpack('h', data.read(2))[0]
        for i in range(0, length):
            key_type = struct.unpack('h', data.read(2))[0]
            key = loader.deserialize(data, type_registry.get(key_type), **kwargs)

            val_type = struct.unpack('h', data.read(2))[0]
            val = loader.deserialize(data, type_registry.get(val_type), **kwargs)

            obj[key] = val

        return obj


# TODO: Optimise for arrays where the values are all the same type. Will only need to write one type identifier for those.
class ArraySerializer(Serializer):
    """
    Array serializer that serializes to binary
    """
    def serialize(self, loader, obj, **kwargs):
        buffer = b''
        buffer += struct.pack('h', len(obj))

        for i in range(0, len(obj)):
            # Write Type
            buffer += struct.pack("h", type_registry.get(type(obj[i])))
            # Write Index
            buffer += struct.pack("h", i)
            # Write item
            buffer += loader.serialize(obj[i], **kwargs)

        return buffer

    def deserialize(self, loader, cls, data, **kwargs):
        obj = []

        length = struct.unpack('h', data.read(2))[0]
        obj.extend(range(length))

        for i in range(0, length):
            item_type = struct.unpack('h', data.read(2))[0]
            item_index = struct.unpack('h', data.read(2))[0]

            obj[item_index] = loader.deserialize(data, type_registry.get(item_type), **kwargs)

        return tuple(obj) if cls is tuple else obj
