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

    def create_value(
        self, first_name: str = "", last_name: str = "", age: int = 0
    ) -> Contact:
        return Contact(first_name=first_name, last_name=last_name, age=age)

    def update_value(
        self,
        value: Contact,
        timestamp: int,
        first_name: str = None,
        last_name: str = None,
        age: int = None,
    ):
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
