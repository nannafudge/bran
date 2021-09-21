"""
Module for bran Loaders
"""
from pathlib import Path

from pybran.decorators import type_registry
from pybran.exceptions import BranFileException, BranSerializerException
from pybran.serializers import IntSerializer, StringSerializer, MappingSerializer, ArraySerializer, \
    BoolSerializer, FloatSerializer, SetSerializer

DEFAULT_SERIALIZER_REGISTRY = {
    bool: BoolSerializer,
    int: IntSerializer,
    float: FloatSerializer,
    str: StringSerializer,
    set: SetSerializer,
    dict: MappingSerializer,
    list: ArraySerializer,
    tuple: ArraySerializer
}


class Loader:
    """
    Loader class responsible for loading/writing objects to files and serializing/deserializing objects
    """

    def __init__(self, serializer_registry=None):
        """
        Initialise a new Loader object

        :param serializer_registry: Mapping of type : Serializer, used to lookup which serializer to use when
        serializing/deserializing. Overrides default serializers.
        """
        if serializer_registry is None:
            serializer_registry = DEFAULT_SERIALIZER_REGISTRY

        self.serializer_registry = serializer_registry
        self._serializer_pool = {}

    def deserialize(self, data, cls=None, **kwargs):
        """
        Attempt to deserialize an object from an input using the registered serializers in `serializer_registry`

        :param data: The data to deserialize
        :param cls: The class to deserialize to, no value needed if Tagging = True
        :param kwargs: Additional arguments to be passed to the deserializers. Options are:
        Tagging = True/False - Whether the data is tagged with class type information

        :return: An instance of :cls: deserialized from :data:
        """
        if kwargs.get("tagging") is True:
            cls_id = self.get_serializer(int).deserialize(self, int, data, **kwargs)

            if not type_registry.contains(cls_id):
                raise BranSerializerException(f"Type ID {cls_id} does not exist/is not registered!", cls_id)

            cls = type_registry.get(cls_id)

        return self.get_serializer(cls).deserialize(self, cls, data, **kwargs)

    def serialize(self, obj, **kwargs):
        """
        Attempt to serialize an object using the registered serializers in `serializer_registry`

        :param obj: The object to serialize
        :param kwargs: Additional arguments to be passed to the deserializers. Options are:
        `Tagging = True/False` - Whether the output data is tagged with class type information

        :return: An serialized instance of :obj:
        """

        cls = obj if isinstance(obj, type) else type(obj)

        tag = b''
        if kwargs.get("tagging") is True:
            tag = self.get_serializer(int).serialize(self, type_registry.get(cls, autoregister=True), **kwargs)

        return tag + self.get_serializer(cls).serialize(self, obj, **kwargs)

    def read(self, path: str, cls: type, **kwargs):
        """
        Attempt to read an object of type :cls: from a file at :param path:

        :param path: String representation of the path of the file to read from
        :param cls: The class to read into
        :param kwargs: Additional arguments to be passed to the deserializer, see
        [[bran.Loader.deserialize]] for more information on accepted arguments

        :return: An instance of :cls: deserialized from the file at :path:
        """
        self._validate_path(path)

        with open(path, 'rb') as file:
            return self.deserialize(file, cls, **kwargs)

    def write(self, path: str, obj: object, **kwargs):
        """
        Attempt to write an object to a file at :param path:

        :param path: String representation of the path of the file to write to
        :param obj: The object to write
        :param kwargs: Additional arguments to be passed to the serializer, see
        [[bran.Loader.serialize]] for more information on accepted arguments
        """
        self._validate_path(path)

        with open(path, 'wb') as file:
            file.write(self.serialize(obj, **kwargs))

    def register(self, cls: type, serializer: type):
        """
        Register a serializer for a type

        :param cls: The type to register the serializer for
        :param serializer: The serializer type to register
        """
        self.serializer_registry[cls] = serializer

    def get_serializer(self, cls: type):
        """
        Returns the serializer registered for type :param cls:, raises
        [[bran.exceptions.BranSerializerException]] if no serializer registered for type.

        Serializers are instantiated and stored in a pool.

        :param cls: The type to get the serializer for

        :return: An instance of the serializer registered for this type
        """
        if not self.serializer_registry.__contains__(cls):
            raise BranSerializerException(f"No serializer registered for class {str(cls)}!", cls)

        serializer = self.serializer_registry[cls]
        if not self._serializer_pool.__contains__(serializer):
            self._serializer_pool[serializer] = serializer.__new__(serializer)

        return self._serializer_pool[serializer]

    def _validate_path(self, path: str):
        """
        Internal method used to validate if a path exists. Raises [[bran.exceptions.BranFileException]] if the path
        is invalid

        :param path: String representation of the path to check
        :param writing: Whether we're writing a file or not, if False, Bran will also check if the File exists to be
        read from
        """
        if not Path(path).is_file():
            raise BranFileException("Invalid file path specified!", path)
