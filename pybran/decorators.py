"""
Module for tagging classes and their fields, as well as enumerating their fields for more efficient
serialization. We need to keep a registry of each classes fields as we don't know from a class definition in python
which attributes are member variables.
"""
from pybran.synchronized import synchronized

class_registry = synchronized({})
type_registry = synchronized({})
name_registry = synchronized({})


class Id:
    """
    Singleton base class for Atomic IDs
    """

    _instance = None

    def __init__(self):
        """
        Not to be called
        """
        raise RuntimeError("Cannot instantiate Singleton class")

    @classmethod
    def instance(cls):
        """

        :return: Atomic ID object instance
        """
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance._id = 0
        return cls._instance

    @synchronized
    def get_id(self):
        """
        Thread Safe
        Returns the next available Atomic ID

        :return:  int
        """
        self._id += 1
        return self._id

    @synchronized
    def reset(self):
        """
        Thread Safe
        Resets the Atomic ID value
        """
        self._id = 0


class TypeId(Id):
    """
    Atomic ID class for tracking Type enumerations
    """

    _instance = None


class NameId(Id):
    """
    Atomic ID class for tracking field Name enumerations
    """

    _instance = None


class Field:
    """
    Temporary class used to indicate a field has been autoregistered
    """

    def __init__(self, val):
        """

        :param val: The value of the field (used to determine field type and set field later post registration)
        """
        self.val = val


def register_class(cls: type, fields=None):
    """

    Register a class and its fields with the registries.
    Ensure its names and types are registered and enumerated if they do not already exist.

    :param cls: The class to register
    :param fields: Mapping of name : type representing the fields of the class. Used when manually registering a class.
    """
    if fields is None:
        fields = {}

    class_registry[cls] = {}
    name_registry[cls] = {}

    register_type(cls)

    NameId.instance().reset()

    if not fields:
        autoregistered_fields = {}

        for name, _field in cls.__dict__.items():
            if isinstance(_field, Field):
                autoregistered_fields[name] = _field.val

        fields.update(autoregistered_fields)

        # Ensure that the fields in the class are set to their intended values that field wrapped
        for name, val in autoregistered_fields.items():
            setattr(cls, name, val)

    for name, val in fields.items():
        # Python allows for fields to be added willy nilly so whatever on this check
        # if not hasattr(cls, name):
        #    raise BranRegistrationException(f"Tried to register unrecognised field, {str(cls)} has no field {name}!", cls)

        register_field(cls, name, val if isinstance(val, type) else type(val))


def register_field(cls: type, name: str, _type: type):
    """

    Registers a classes field with the class_registry, and ensures its name and type have a registered enumeration.

    :param cls: The class who's field we are registering
    :param name: The name of the field
    :param _type: The type of the value of the field
    """
    class_registry[cls][name] = _type

    register_type(_type)
    register_field_name(cls, name)


def register_type(_type: type):
    """

    Ensures that type _type has an enumeration registered in the type_registry. This is used for serialization later,
    only the enumeration/id of the type is used to save space if storing type is necessary.

    If the enumeration does not yet exist for type _type, a new enumeration will be generated from
    :cls:`TypeId <pybran.decorators.TypeId>`

    :param _type: The type we're registering an enumeration for
    """
    if not type_registry.__contains__(_type):
        type_registry[_type] = TypeId.instance().get_id()
    type_registry[type_registry[_type]] = _type


def register_field_name(cls: type, name: str):
    """
    Ensures that field :name: from the class :cls: has an enumeration registered in the name_registry.
    This is used for serialization later, only the enumeration/id of the field name is used to save space.

    If no enumeration exists for the field, then a new enumeration will be generated from
    :cls:`NameId <pybran.decorators.NameId>`

    :param cls: The class who's field we're registering
    :param name: The name of the field we're registering an enumeration for
    """
    if not name_registry[cls].__contains__(name):
        name_registry[cls][name] = NameId.instance().get_id()
    name_registry[cls][name_registry[cls][name]] = name


def schema(cls):
    """

    Schema class decorator, to be used to declare a class as a Schema to be registered internally

    :param cls: The class to be registered
    :return: The registered class
    """
    register_class(cls)

    return cls


def field(val):
    """

    Field value decorator, to be used to declare a member as a field member of a class

    Returns a Field object, so when registering a class, the class knows which attributes/members should be
    registered ahead of time. The field value will be appropriately replaced/reset in the registration process
    once the Schema has registered this field.

    :param val: The value of the field
    :return: The value wrapped in a Field object
    """
    return Field(val)
