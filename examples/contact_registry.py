import json
import sys
from pathlib import Path

# Add package root path so generic_key_value_registry is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from generic_key_value_registry import Registry, encode, decode
from contact import Contact


class ContactRegistry(Registry[str, Contact]):

    def __str__(self):
        return f"ContactRegistry: {self.get_all_entries()}"

    def _update_value(self, value: Contact, new_value: Contact) -> bool:
        updated = False
        if new_value.first_name and value.first_name != new_value.first_name:
            value.first_name = new_value.first_name
            updated = True
        if new_value.last_name and value.last_name != new_value.last_name:
            value.last_name = new_value.last_name
            updated = True
        if new_value.age and value.age != new_value.age:
            value.age = new_value.age
            updated = True
        return updated


    def serialize_key(self, key: str) -> str:
        return encode(key)

    def deserialize_key(self, s: str) -> str:
        return decode(s)

    def serialize_value(self, value: Contact) -> str:
        return json.dumps(
            {
                "first_name": value.first_name,
                "last_name": value.last_name,
                "age": value.age,
            }
        )

    def _deserialize_value_1(self, s: str) -> Contact:
        d = json.loads(s)
        return Contact(
            first_name=d.get("first_name", ""),
            last_name=d.get("last_name", ""),
            age=d.get("age", 0),
        )

    def deserialize_value(self, version: int, s: str) -> Contact:
        if version == 1:
            return self._deserialize_value_1(s)
        else:
            raise ValueError(f"Unknown version: {version}")
