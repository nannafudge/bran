import enum
from pathlib import Path

from bran.exceptions import BranFileException
from bran.synchronized import synchronized

class Loader:
    class Flags(enum.Enum):
        BINARY = "b",
        TEXT = "t"

    def __init__(self, serializer_registry={}, type_registry={}):
        self._serializers = serializer_registry
        self._types = type_registry

    def deserialize(self, cls, data, **kwargs):
        return self._serializers.get(cls).deserialize(self, cls, data, **kwargs)

    def serialize(self, obj, **kwargs):
        cls = kwargs.get("cls", None)
        cls = obj.__class__ if cls is None else cls

        return self._serializers.get(cls).serialize(loader=self, obj=obj, **kwargs)

    def read(self, path, cls, **kwargs):
        self._validate_path(path)
        raw = kwargs.get("raw")

        data = None
        with self._open(path, 'r', **kwargs) as file:
            if raw:
                return self.deserialize(cls, file, **kwargs)
            data = file.read()

        return self.deserialize(cls, data, **kwargs)

    def write(self, path, obj, **kwargs):
        self._validate_path(path)

        with self._open(path, 'w', **kwargs) as file:
            file.write(self.deserialize(obj, **kwargs))

    @synchronized
    def _open(self, path, access, **kwargs):
        mode = kwargs.get("flags", Loader.Flags.TEXT)

        flags = f"{access}{str(mode)}"

        return open(path, flags)

    def _validate_path(self, path):
        if not Path(path).exists():
            raise BranFileException("File path does not exist!", path)
