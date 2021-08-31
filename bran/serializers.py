import struct

from bran.decorators import class_registry, type_registry, name_registry
from bran.exceptions import BranSerializerException


class Serializer:
    def serialize(self, loader, obj, **kwargs):
        pass

    def deserialize(self, loader, cls, input, **kwargs):
        pass


class DefaultSerializer(Serializer):
    def serialize(self, loader, obj, **kwargs):
        fields = class_registry.get(obj.__class__, None)

        if fields is None:
            raise BranSerializerException("No fields registered for type", obj)

        # TODO: Add ability to unpack unregistered types?
        # buffer = loader.serialize(type_registry.get(obj.__class__), kwargs)
        buffer = b''

        for name, field in fields:
            buffer += loader.serialize(loader, name_registry.get(name), kwargs)
            buffer += loader.serialize(loader, getattr(obj, name), kwargs)

        return buffer

    def deserialize(self, loader, cls, input, **kwargs):
        fields = class_registry.get(cls, None)

        if fields is None:
            raise BranSerializerException("No fields registered for type", cls)

        obj = cls.__new__(cls)
        for name, field in fields:
            setattr(obj, name, loader.deserialize(loader, type_registry.get(field._id), input, kwargs))

        return obj


class IntSerializer(Serializer):
    def serialize(self, loader, obj, **kwargs):
        return struct.pack('i', obj)

    def deserialize(self, loader, cls, input, **kwargs):
        return struct.unpack('i', input.read(4))


class StringSerializer(Serializer):
    def serialize(self, loader, obj, **kwargs):
        return struct.pack('h', len(obj)) + bytes(obj, "UTF-8")

    def deserialize(self, loader, cls, input, **kwargs):
        len = struct.unpack('h', input.read(2))

        return input.read(len).decode("UTF-8")


# TODO: Optimise for maps where k,v pairs are strictly typed, so will only need to write one key_id, val_id for entire map
class MappingSerializer(Serializer):
    def serialize(self, loader, obj, **kwargs):
        buffer = b''
        buffer += struct.pack('h', len(obj))

        for key, value in obj.items():
            buffer += struct.pack('h', type_registry.get(type(key)))
            buffer += loader.serialize(loader, key, kwargs)

            buffer += struct.pack('h', type_registry.get(type(value)))
            buffer += loader.serialize(loader, value, kwargs)

    def deserialize(self, loader, cls, input, **kwargs):
        obj = {}

        length = struct.unpack('h', input.read(2))[0]
        for i in range(0, length):
            key_type = struct.unpack('h', input.read(2))[0]
            key = loader.deserialize(loader, type_registry.get(key_type), input, kwargs)

            val_type = struct.unpack('h', input.read(2))[0]
            val = loader.deserialize(loader, type_registry.get(val_type), input, kwargs)

            obj[key] = val

        return obj


# TODO: Optimise for arrays where the values are all the same type. Will only need to write one type identifier for those.
class ArraySerializer(Serializer):
    def serialize(self, loader, obj, **kwargs):
        buffer = b''
        buffer += struct.pack('h', len(obj))

        for i in range(0, len(obj)):
            # Write Type
            buffer += struct.pack("h", type_registry.get(type(obj[i])))
            # Write Index
            buffer += struct.pack("h", i)
            # Write item
            buffer += loader.serialize(loader, obj[i], kwargs)

        return buffer

    def deserialize(self, loader, cls, input, **kwargs):
        obj = []

        length = struct.unpack('h', input.read(2))[0]
        for i in range(0, length):
            item_type = struct.unpack('h', input.read(2))[0]
            item_index = struct.unpack('h', input.read(2))[0]

            obj[item_index] = loader.deserialize(loader, type_registry.get(item_type), input, kwargs)

        return obj
