from bran.synchronized import synchronized

class_registry = {}
type_registry = {}
name_registry = {}


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


class TypeId(Id):
    pass


class NameId(Id):
    pass


def schema(cls):
    class_registry[cls] = {}

    for name, field in cls.__dict__.items():
        if isinstance(field, Field):
            _name = field._name if field._name is not None else name

            class_registry[cls][_name] = field

            type_registry[field._val.__class__] = field._id
            type_registry[field._id] = field._val.__class__

            name_registry[_name] = name_registry.get(_name, NameId.instance().get_id())
            name_registry[name_registry.get(_name)] = _name

    return cls


class Field:
    def __init__(self, val, name):
        self._id = type_registry.get(val.__class__, TypeId.instance().get_id())
        self._name = name
        self._val = val


def field(val, name=None):
    return Field(val, name)
