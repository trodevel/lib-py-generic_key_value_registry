from dataclasses import dataclass


@dataclass
class Contact:
    first_name: str = ""
    last_name: str = ""
    age: int = 0
