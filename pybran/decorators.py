"""
Module for tagging classes and their fields, as well as enumerating their fields for more efficient
serialization. We need to keep a registry of each classes fields as we don't know from a class definition in python
which attributes are member variables.
"""
from pybran.exceptions import BranRegistrationException
from pybran.synchronized import synchronized


@synchronized
class Id:
    """
    Singleton base class for Atomic IDs
    """

    _instance = None

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Id, cls).__new__(cls, *args, **kwargs)
            cls._instance._id = 0
        return cls._instance

    def get_id(self):
        """
        Thread Safe
        Returns the next available Atomic ID

        :return:  int
        """
        self._id += 1

        return self._id

    def reset(self):
        """
        Resets the internal atomic counter
        """
        self._id = 0


@synchronized
class TypeId(Id):
    """
    Atomic ID class for tracking Type enumerations
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        return super(TypeId, cls).__new__(cls, *args, **kwargs)


@synchronized
class NameId(Id):
    """
    Atomic ID class for tracking field Name enumerations
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        return super(NameId, cls).__new__(cls, *args, **kwargs)


class Field:
    """
    Temporary class used to indicate a field has been autoregistered
    """

    def __init__(self, val):
        """

        :param val: The value of the field (used to determine field type and set field later post registration)
        """
        self.val = val


@synchronized
class Registry:
    """
    Class for storing mirrored key:value pairs that can be queried later on. Can be provided with an autogeneration
    function to automatically generate registry entries.
    """
    def __init__(self, default_value_generator: callable):
        """
        :param default_value_generator: The default Registry value generator that will be used when autoregistering
        """
        self.default_value_generator = default_value_generator

        self.registry = {}

    def get(self, key, autoregister=False):
        """
        Get an entry from the registry. Optionally, generate an entry if one is missing before returning.

        Can raise a BranRegistrationException if no entry is present and autoregister=False

        :param key: The key to query for
        :param autoregister: Whether to automatically generate an entry for the key

        :return: The registry entry for the key
        """
        if not self.contains(key):
            if autoregister:
                self.add(key)
            else:
                raise BranRegistrationException(f"No entry for {key} registered!", key)

        return self.registry.get(key)

    def add(self, key, value=None):
        """
        Add an entry to the registry (if not already present) and generate a value using the :default_value_generator:

        Can optionally provide the entry value for the registry key if needed (i.e. Registering a specific entity for a
        key)

        :param key: The key to add an entry for
        :param value: Optional value to specify (otherwise generated with default_value_generator)
        """
        if not self.contains(key):
            if value is None:
                value = self.default_value_generator(key)

            self.set(key, value)
            self.set(self.get(key), key)

    def set(self, key, value):
        """
        Set a key in the registry to the specified value

        :param key: The key to set
        :param value: The value to set the key to
        """
        self.registry.__setitem__(key, value)

    def remove(self, key):
        """
        Remove a key from the registry, returns the associated removed value too if the key exists in the Registry

        :param key: The key to remove
        :return: The value removed, if present
        """
        if self.contains(key):
            return self.registry.pop(key)

    def clear(self):
        """
        Clear the registry of all values
        """
        self.registry.clear()

    def contains(self, key):
        """
        Whether the registry contains an entry for the key

        :param key: The key to check
        :return: Whether the registry contains an entry for the key
        :rtype: bool
        """
        return self.registry.__contains__(key)

    def items(self):
        """
        Get the items contained within the registry

        :return: The items contained within the registry
        """
        return self.registry.items()

    def keys(self):
        """
        :return: All registry keys
        """
        return self.registry.keys()

    def values(self):
        """
        :return: All registry entries
        """
        return self.registry.values()

    def __len__(self, *args, **kwargs):
        """
        :return: The length of the registry
        :rtype: int
        """
        return self.registry.__len__()


class_registry = Registry(default_value_generator=lambda k: Registry(default_value_generator=lambda k2: None))
type_registry = Registry(default_value_generator=lambda k: TypeId().get_id())
name_registry = Registry(default_value_generator=lambda k: Registry(default_value_generator=lambda k2: NameId().get_id()))


def refresh():
    """
    Refresh the class registry and repopulate the type and name registry with the latest mapping values.

    Useful when redefining the default value generators and using decorators, as the decorators are ran when importing
    pybran, and redefining the default generators can only be done post-import.
    """
    classes = {}

    # It should be fine to reuse the type definitions for fields since field type definitions should NEVER change at
    # runtime. This also allows bespoke user mappings to be preserved (classes registered without decorators/manually).
    for cls in class_registry.keys():
        if isinstance(cls, type):
            classes.__setitem__(cls, {})
            for _field in class_registry.get(cls).items():
                classes.get(cls).__setitem__(_field[0], _field[1])

    class_registry.clear()
    type_registry.clear()
    name_registry.clear()

    TypeId().reset()
    NameId().reset()

    for definition in classes.items():
        register_class(definition[0], definition[1])


def register_class(cls: type, fields=None):
    """
    Register a class and its fields with the registries.
    Ensure its names and types are registered and enumerated if they do not already exist.

    :param cls: The class to register
    :param fields: Mapping of name : type representing the fields of the class. Used when manually registering a class.
    """

    if fields is None:
        fields = {}

    class_registry.add(cls)
    name_registry.add(cls)
    type_registry.add(cls)

    NameId().reset()

    if not fields:
        autoregistered_fields = {}

        for name, _field in cls.__dict__.items():
            if isinstance(_field, Field):
                autoregistered_fields.__setitem__(name, _field.val)

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
    class_registry.get(cls).set(name, _type)

    type_registry.add(_type)
    register_field_name(cls, name)


def register_field_name(cls: type, name: str):
    """
    Ensures that field :name: from the class :cls: has an enumeration registered in the name_registry.
    This is used for serialization later, only the enumeration/id of the field name is used to save space.

    If no enumeration exists for the field, then a new enumeration will be generated from
    :cls:`NameId <pybran.decorators.NameId>`

    :param cls: The class who's field we're registering
    :param name: The name of the field we're registering an enumeration for
    """
    name_registry.get(cls).add(name)


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
