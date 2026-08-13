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

    def _update_value(self, value: Contact, new_value: Contact):
        if new_value.first_name:
            value.first_name = new_value.first_name
        if new_value.last_name:
            value.last_name = new_value.last_name
        if new_value.age:
            value.age = new_value.age

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

    def deserialize_value(self, s: str) -> Contact:
        d = json.loads(s)
        return Contact(
            first_name=d.get("first_name", ""),
            last_name=d.get("last_name", ""),
            age=d.get("age", 0),
        )
