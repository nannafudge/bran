# (Py)Bran

(Py)Bran - Boring, plain and simple python binary serialization/deserialization library

Its called (Py)Bran because Bran was taken. It does (cereal)ization. Yes. Also because Bran (the ceareal) is boring like
this library.

[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)
[![PyPI Version](https://img.shields.io/pypi/v/pybran.svg)](https://pypi.python.org/pypi/pybran/)
[![PyPI Versions](https://img.shields.io/pypi/pyversions/pybran.svg)](https://pypi.python.org/pypi/pybran/)
[![PyPI Status](https://img.shields.io/pypi/status/pybran.svg)](https://pypi.python.org/pypi/pybran/)

[![CI Status](https://github.com/nannafudge/bran/actions/workflows/ci.yml/badge.svg)](https://github.com/nannafudge/bran/actions/workflows/ci.yml)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
![PyLint Score](https://gist.githubusercontent.com/nannafudge/1537485abce2009252beb4f346dea43b/raw/pylint.svg)
![Coverage %](https://gist.githubusercontent.com/nannafudge/1537485abce2009252beb4f346dea43b/raw/coverage.svg)

## Installing

```
pip install pybran
```

## Using

### Registering your Schemas

In order for Bran to work with complex objects, it needs to know the object Schema.
Schemas can be defined in two ways:
- Automatically with Decorators
- Manually

#### Automatically with Decorators
```python
from pybran import schema, field

@schema
class MyClass:
    test = field(1)
    other = field(MyClass2())

@schema
class MyClass2:
    test2 = field(2)
```

#### Manually
```python
from pybran import register_class

class MyClass:
    test = 1
    other = MyClass2()

class MyClass2:
    test2 = 2
    
register_class(MyClass2, {"test2": MyClass2.test2})
register_class(MyClass, {"test": MyClass.test, "other": MyClass.other})
```

### Registering field aliases

Bran generates an enumeration for each field so it knows which field it's deserializing when doing so.
Writing an enumeration is more efficient than writing the field name itself.

If you want to override the enumeration bran generates, you can do so by specifying the `alias` parameter when
registering a field. You can also manually register aliases if need be. Registering with annotations is done like so:

```python
@schema
class MyClass:
    test = field(1, alias=b'\x05')
```

Manual registration can be done like so:

```python
from pybran import register_class

class MyClass:
    test = 1
    
register_class(MyClass, {"test2": MyClass.test}, {"test2": b'\x05'})
```

Aliases and field information can be fetched from the `ClassDefinition` definition stored in the `class_registry`

```python
from pybran import class_registry, ClassDefinition

@schema
class MyClass:
    test = field(1)

class_definition: ClassDefinition = class_registry.get(MyClass)
```

The `ClassDefinition` object contains two internal `Registry` objects:

- `fields`: Tracks the class fields and their types
- `aliases`: Aliases registered for the class fields

```python
from pybran import class_registry, ClassDefinition

@schema
class MyClass:
    test = field(1)
    test2 = field(1, alias=b'\x05')

class_definition: ClassDefinition = class_registry.get(MyClass)

class_definition.fields.get("test") # Returns type(int)
class_definition.fields.get("test2") # Returns type(int)

class_definition.aliases.get("test") # Returns 1 (first registered enumeration)
class_definition.aliases.get("test2") # Returns b'\x05'

class_definition.aliases.get(1) # Returns "test"
class_definition.aliases.get(b'\x05') # Returns "test2"
```
### Serializing

#### Registering Serializers

Bespoke Serializers can be registered with the `Loader` instance using the `Loader.register` method.

```python
from pybran.loaders import Loader
from pybran.serializers import DefaultSerializer

loader = Loader()

# Register the type MyClass to use the serializer DefaultSerializer 
loader.register(MyClass, DefaultSerializer)
```

Bran automatically comes configured with a serializer registry that maps the following types:

```python
from pybran.serializers import *

{
    bool: BoolSerializer,
    int: IntSerializer,
    float: FloatSerializer,
    str: StringSerializer,
    set: SetSerializer,
    dict: MappingSerializer,
    list: ArraySerializer,
    tuple: ArraySerializer
}
```

When importing the `Loader`, these are already preconfigured. If you wish to specify your own serializer registry to use
upon instantiation, then you can override it when creating a new `Loader` object.

```python
from pybran.loaders import Loader
from pybran.exceptions import BranSerializerException

serializers = {
    int: MyCustomSerializer
}

loader = Loader(serializers)

# Using MyCustomSerializer
try:
    serialized = loader.serialize(1)
except BranSerializerException as e:
    print(e)
```


#### Serializing Directly

Serializing an object is as simple as calling the `Loader.serialize` method

Any serialization errors will raise a `BranSerializerException`

```python
from pybran.loaders import Loader
from pybran.exceptions import BranSerializerException

loader = Loader()

try:
    serialized = loader.serialize(1)
except BranSerializerException as e:
    print(e)
```

#### Deserializing Directly

Deserializing is just as simple

Any deserialization errors will raise a `BranSerializerException`


```python
import io

from pybran.loaders import Loader
from pybran.exceptions import BranSerializerException

loader = Loader()

serialized = b'\x00\x00\x00\x00'
try:
    myint = loader.deserialize(io.BytesIO(serialized), int)
except BranSerializerException as e:
    print(e)
```

#### Serializing with Automatic Type Tagging

When serializing/deserializing a type, type information can be configured to be stored so the deserializer
automatically knows which object to deserialize to.

This can be done by passing the `tagging = True` kwarg when calling serialize/deserialize

```python
import io

from pybran.serializers import DefaultSerializer
from pybran.loaders import Loader

loader = Loader()
loader.register(MyClass, DefaultSerializer)

myobj = MyClass()

serialized = loader.serialize(myobj, tagging=True)
myobj_deserialized = loader.deserialize(io.BytesIO(serialized), tagging=True)
```

#### Reading from a file

The `Loader` is also capable of reading and writing to a file

Can raise a `BranFileException`


```python
from pybran.loaders import Loader
from pybran.serializers import DefaultSerializer
from pybran.exceptions import BranSerializerException, BranFileException

loader = Loader()
loader.register(MyClass, DefaultSerializer)

try:
    myobject = loader.read("path/my_file", MyClass)
except (BranSerializerException, BranFileException) as e:
    print(e)
```

#### Writing to a file

Can raise a `BranFileException`

```python
from pybran.loaders import Loader
from pybran.serializers import DefaultSerializer
from pybran.exceptions import BranSerializerException, BranFileException

loader = Loader()
loader.register(MyClass, DefaultSerializer)

myobject = MyClass()

try:
    loader.write("path/my_file", myobject)
except (BranSerializerException, BranFileException) as e:
    print(e)
```

### Writing a Custom Serializer

Writing a custom serializer can be done by extending the `Serializer` class, and registering the class
with your `Loader` instance.

```python
from pybran.serializers import Serializer
from pybran.loaders import Loader

class MyCustomSerializer(Serializer):
    def serialize(self, loader, obj, **kwargs):
        # Implement custom serialization logic here

    def deserialize(self, loader, cls, data, **kwargs):
        # Implement custom deserialization logic here

loader = Loader()
loader.register(MyClass, MyCustomSerializer)
```

### Overriding automatic Type ID generation

PyBran uses a cache to enumerate types with an identification token. This cache takes the form of a symmetric dict.
This allows PyBran, when its necessary to store type information, to write the enumeration/ID of the Type,
rather than the entire type information.

By default, Type IDs are generated with an Atomic counter. When PyBran registers a class, it automatically registers an
enumeration for the class itself and any unseen types contained within.

`pybran/decorators.py`
```python
...

type_registry = Registry(lambda k: TypeId().get_id())

...
```

This can be overridden by changing the `default_value_generator` of the type registry, like so:

```python
import pybran

bespoke_map = {
    int: b'I',
    float: b'L'
}

def generate_key(k: type):
    return bespoke_map.get(type, pybran.TypeId().get_id())

pybran.type_registry.default_value_generator = generate_key
pybran.refresh()
```

Refresh *MUST* be called to refresh the registry caches if you update the default value generator functions.
Otherwise the registry will contain both old and new autogenerated values.