from collections import namedtuple

from bran.exceptions import BranRegistrationException
from bran.synchronized import synchronized

class_registry = synchronized({})
type_registry = synchronized({})
name_registry = synchronized({})


class Id:
    _instance = None

    def __init__(self):
        raise RuntimeError("Cannot instantiate Singleton class")

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance._id = 0
        return cls._instance

    @synchronized
    def get_id(self):
        self._id += 1
        return self._id

    @synchronized
    def reset(self):
        self._id = 0


class TypeId(Id):
    _instance = None


class NameId(Id):
    _instance = None


class Field:
    def __init__(self, val):
        self._val = val


def register_class(cls: type, fields=None):
    if fields is None:
        fields = {}

    class_registry[cls] = {}
    name_registry[cls] = {}

    register_type(cls)

    NameId.instance().reset()

    if not fields:
        autoregistered_fields = {}

        for name, field in cls.__dict__.items():
            if isinstance(field, Field):
                autoregistered_fields[name] = field._val

        fields.update(autoregistered_fields)
        for name, val in autoregistered_fields.items():
            setattr(cls, name, val)

    for name, val in fields.items():
        # Python allows for fields to be added willy nilly so whatever on this check
        # if not hasattr(cls, name):
        #    raise BranRegistrationException(f"Tried to register unrecognised field, {str(cls)} has no field {name}!", cls)

        register_field(cls, name, val if isinstance(val, type) else type(val))


def register_field(cls: type, name: str, value: type):
    class_registry[cls][name] = value

    register_type(value)
    register_field_name(cls, name)


def register_type(_type: type):
    if not type_registry.__contains__(_type):
        type_registry[_type] = TypeId.instance().get_id()
    type_registry[type_registry[_type]] = _type

def register_field_name(cls: type, name: str):
    if not name_registry[cls].__contains__(name):
        name_registry[cls][name] = NameId.instance().get_id()
    name_registry[cls][name_registry[cls][name]] = name


def schema(cls):
    register_class(cls)

    return cls


def field(val):
    return Field(val)
