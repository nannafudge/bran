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

    def __init__(self, val, alias=None):
        """

        :param val: The value of the field (used to determine field type and set field later post registration)
        """
        self.val = val
        self.alias = alias


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


class ClassDefinition:
    def __init__(self, cls, fields_registry: Registry = None, aliases_registry: Registry = None):
        self.cls = cls

        if not fields_registry:
            fields_registry = Registry(lambda k: NameId().get_id())

        if not aliases_registry:
            aliases_registry = Registry(lambda k: None)

        self.fields = fields_registry
        self.aliases = aliases_registry

    def clear(self):
        self.fields.clear()
        self.aliases.clear()


class_registry = Registry(lambda cls: ClassDefinition(cls))
type_registry = Registry(lambda k: TypeId().get_id())


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
            classes.get(cls).__setitem__('fields', {})
            classes.get(cls).__setitem__('aliases', {})

            class_definition = class_registry.get(cls)

            for _field in class_definition.fields.items():
                classes.get(cls).get('fields').__setitem__(_field[0], _field[1])

            for _alias in class_definition.aliases.items():
                classes.get(cls).get('aliases').__setitem__(_alias[0], _alias[1])

    class_registry.clear()
    type_registry.clear()

    TypeId().reset()
    NameId().reset()

    for cls, definition in classes.items():
        register_class(cls, definition.get('fields'), definition.get('aliases'))


def register_class(cls: type, fields=None, aliases=None):
    """
    Register a class and its fields with the registries.
    Ensure its names and types are registered and enumerated if they do not already exist.

    :param cls: The class to register
    :param fields: Mapping of name : type representing the fields of the class. Used when manually registering a class.
    :param aliases: Mapping of field name : alias
    """

    if fields is None:
        fields = {}

    if aliases is None:
        aliases = {}

    class_registry.add(cls)
    type_registry.add(cls)

    NameId().reset()

    if not fields:
        autoregistered_fields = {}

        for name, _field in cls.__dict__.items():
            if isinstance(_field, Field):
                autoregistered_fields.__setitem__(name, _field.val)

                if _field.alias:
                    aliases.__setitem__(name, _field.alias)

        fields.update(autoregistered_fields)

        # Ensure that the fields in the class are set to their intended values that field wrapped
        for name, val in autoregistered_fields.items():
            setattr(cls, name, val)

    for name, val in fields.items():
        # Python allows for fields to be added willy nilly so whatever on this check
        # if not hasattr(cls, name):
        #    raise BranRegistrationException(f"Tried to register unrecognised field, {str(cls)} has no field {name}!", cls)
        if not aliases.__contains__(name):
            aliases.__setitem__(name, NameId().get_id())

        register_field(cls, name, val if isinstance(val, type) else type(val))

    for field_name, alias in aliases.items():
        register_alias(cls, field_name, alias)


def register_field(cls: type, name: str, _type: type):
    """

    Registers a classes field with the class_registry, and ensures its name and type have a registered enumeration.

    :param cls: The class who's field we are registering
    :param name: The name of the field
    :param _type: The type of the value of the field
    """
    class_registry.get(cls).fields.set(name, _type)
    type_registry.add(_type)


def register_alias(cls: type, name: str, alias=None):
    """

    Registers an Alias for a class field. This will be used when serializing instead of the actual name.

    If no alias is specified, an enumeration of the name will be generated.
    This allows us to save space by writing this enumeration over writing the name itself.

    :param cls: The class who's field we are registering
    :param name: The name of the field
    :param alias: OPTIONAL: The alias of the field
    """

    # If None is specified, an alias is autogenerated using the auto_generate_function provided to the Aliases registry
    class_registry.get(cls).aliases.add(name, alias)


def schema(cls):
    """

    Schema class decorator, to be used to declare a class as a Schema to be registered internally

    :param cls: The class to be registered
    :return: The registered class
    """
    register_class(cls)

    return cls


def field(val, alias=None):
    """

    Field value decorator, to be used to declare a member as a field member of a class

    Returns a Field object, so when registering a class, the class knows which attributes/members should be
    registered ahead of time. The field value will be appropriately replaced/reset in the registration process
    once the Schema has registered this field.

    :param val: The value of the field
    :param alias: OPTIONAL: Optional alias to use in place of the actual field name during serialization
    :return: The value wrapped in a Field object
    """
    return Field(val, alias)
