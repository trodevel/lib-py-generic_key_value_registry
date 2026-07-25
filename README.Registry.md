# Registry (GKVR - Generic Key-Value Registry)

The `Registry` is a generic data structure designed to track items over time using a standardized approach for metadata (`BookKeeping`) and user-defined state (`Value`). It is deeply inspired by C++ template programming and custom serialization patterns.

## Architecture

The Python implementation mimics the behavior of C++ templates by allowing developers to subclass the generic `Registry[K, V]` base class and define their own value structures and serialization hooks. 

### C++ Inspiration

In C++, a registry might look like:

```cpp
namespace gkvr {
    template <class Key, class V>
    class Registry {
        // Implementation details
    };
}
```

Python achieves this template-like behavior using `typing.Generic`:

```python
from typing import TypeVar, Generic

K = TypeVar('K')
V = TypeVar('V')

class Registry(Generic[K, V]):
    # ...
```

### BookKeeping (Metadata)

The `Registry` inherently maintains metadata for every key. This `BookKeeping` structure is purely internal and should not be operated on directly by "user" classes.
- `created`: The epoch timestamp when the entry was first seen.
- `last_seen`: The epoch timestamp when the entry was most recently seen.
- `changed`: The epoch timestamp when the state of the entry last changed.

The `add_or_update` method handles the logic for appropriately updating these timestamps on every transaction.

### Serialization & Deserialization

The `Registry` utilizes a plaintext file format for storage (`.dat`), deliberately restricting each registry entry to exactly one line. This ensures that the data is trivial to traverse using command-line tools like `grep`.

In C++, serialization is often implemented via function overloading:

```cpp
namespace gkvr {
    ostream & serialize(ostream & os, const MyKey & key);
    ostream & serialize(ostream & os, const MyValue & value);
    std::size_t get_serialization_version(const MyValue & e);
}
```

In this Python version, these operations are provided as virtual "hook" methods that subclasses are expected to override:

- `serialize_key(key: K) -> str`
- `deserialize_key(s: str) -> K`
- `serialize_value(value: V) -> str`
- `deserialize_value(s: str) -> V`
- `get_serialization_version(value: V) -> int`

### String Codec

To allow clean space-separated values on a single line, `string_codec.py` provides `encode()` and `decode()` functions (mirroring C++ equivalents). These encode string keys by converting spaces to `+`, `+` to `++`, `\` to `\\`, and newline characters to literal `\n` characters prior to writing them to the file. 

This guarantees that fields safely remain on the same line and don't break the space-separated integrity.

### Example Usage

To use the Registry, subclass it and implement the initialization and update hooks for your specific type:

```python
from registry import Registry
from counter_stat import CounterStat

class TypeCounterRegistry(Registry[str, CounterStat]):
    def create_value(self, type_id: int) -> CounterStat:
        return CounterStat()

    def update_value(self, value: CounterStat, timestamp: int, type_id: int):
        value.counts[type_id] += 1
        
    def serialize_value(self, value: CounterStat) -> str:
        import json
        return json.dumps(value.counts)
```
