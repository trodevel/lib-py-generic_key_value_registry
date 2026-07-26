from dataclasses import dataclass

@dataclass
class BookKeeping:
    created: int
    last_seen: int
    changed: int
