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

The `add_or_update_ts` method handles the logic for appropriately updating these timestamps on every transaction.

---

## API & Core Methods

### Abstract / Hook Methods
Subclasses are expected to override or customize these operations:

* `create_value(*args, **kwargs) -> V`: Abstract factory method to instantiate a new value object.
* `update_value(value: V, timestamp: int, *args, **kwargs)`: Abstract method to update an existing value instance.
* `get_serialization_version(value: V) -> int`: Returns the content version format (defaults to `1`).
* `serialize_key(key: K) -> str`: Converts key to string (defaults to `str(key)`).
* `deserialize_key(s: str) -> K`: Converts string back to key object.
* `serialize_value(value: V) -> str`: Converts value to string (defaults to `str(value)`).
* `deserialize_value(s: str) -> V`: Converts string back to value object.
* `serialize_bookkeeping(bk: BookKeeping) -> str`: Converts `BookKeeping` timestamps to space-delimited string (`"created last_seen changed"`).
* `deserialize_bookkeeping(s: str) -> BookKeeping`: Restores `BookKeeping` object from space-delimited string.

### Operations & Lifecycle Methods

* `add_or_update_ts(key: K, timestamp: int, *args, **kwargs)`: Adds a key if missing or updates metadata (`created`, `last_seen`, `changed`) and value payload.
* `has(key: K) -> bool`: Checks whether a given key exists in the registry.
* `get(key: K) -> V`: Returns the value for `key` without `BookKeeping` metadata. Raises a `KeyError` if the key is not found.
* `delete(key: K)`: Removes a key-value entry from memory.
* `expire_keys(current_timestamp: int)`: Purges entries whose `last_seen` timestamp exceeds `expiration_period_days` (if `must_expire_keys` is enabled in configuration).
* `get_all_entries() -> Dict[K, Tuple[BookKeeping, V]]`: Returns the complete dictionary of entries mapping keys to `(BookKeeping, Value)` tuples.
* `save()`: Writes the current header and content to disk if configuration option `is_active` is enabled.

### Internal Load/Save Mechanics

* `_load()` & `_load_header()` / `_load_content()`: Handles `.dat` header verification (`GKVR` magic header check) and line parsing during instantiation if `is_active` is set.
* `_save_header()` & `_save_content()`: Writes header details (magic, version, size) followed by single-line representations of each entry.

---

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

### Configuration

`Config` dataclass attributes:
* `is_active`: Controls whether file load and save operations are executed.
* `allow_missing_file`: If `True`, suppresses error when the file does not exist on disk during initial load.
* `filename`: Target filepath for reading and writing data.
* `must_expire_keys`: Toggles automated expiration logic.
* `expiration_period_days`: Lifespan window (in days) evaluated against entry `last_seen` timestamp.

### Example Usage

A complete usage example is available in the `examples/` directory:

- `examples/contact.py`: Dataclass defining `Contact` with `first_name`, `last_name`, and `age` attributes.
- `examples/contact_registry.py`: Implements `ContactRegistry(Registry[str, Contact])` with custom key and value serialization.
- `examples/usage_example.py`: Demonstration script illustrating instantiation, entry updates, saving to disk, and reloading.

#### Environment Setup & Running the Example

Make sure the library path is exported in your environment:

```bash
export PYTHONPATH=$PYTHONPATH:/path/to/libs/python
python3 examples/usage_example.py
```

#### Code Snippet

```python
import json
from dataclasses import dataclass
from generic_key_value_registry import Registry, Config, encode, decode
from contact import Contact

class ContactRegistry(Registry[str, Contact]):
    def create_value(self, first_name: str = "", last_name: str = "", age: int = 0) -> Contact:
        return Contact(first_name=first_name, last_name=last_name, age=age)

    def update_value(self, value: Contact, timestamp: int, first_name: str = None, last_name: str = None, age: int = None):
        if first_name is not None:
            value.first_name = first_name
        if last_name is not None:
            value.last_name = last_name
        if age is not None:
            value.age = age

    def serialize_key(self, key: str) -> str:
        return encode(key)

    def deserialize_key(self, s: str) -> str:
        return decode(s)

    def serialize_value(self, value: Contact) -> str:
        return json.dumps({
            "first_name": value.first_name,
            "last_name": value.last_name,
            "age": value.age
        })

    def deserialize_value(self, s: str) -> Contact:
        d = json.loads(s)
        return Contact(
            first_name=d.get("first_name", ""),
            last_name=d.get("last_name", ""),
            age=d.get("age", 0)
        )

# Instantiation with config
config = Config(
    is_active=True,
    allow_missing_file=True,
    filename="data.dat",
    must_expire_keys=True,
    expiration_period_days=30
)

registry = ContactRegistry(config)
registry.add_or_update_ts("user_1", timestamp=1700000000, first_name="Alice", last_name="Smith", age=30)
registry.save()
```
