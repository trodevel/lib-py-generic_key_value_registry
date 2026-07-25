import os
from typing import TypeVar, Generic, Dict, Tuple
from dataclasses import dataclass

K = TypeVar('K')
V = TypeVar('V')

@dataclass
class Config:
    is_active: bool
    allow_missing_file: bool
    filename: str
    must_expire_keys: bool
    expiration_period_days: int

@dataclass
class BookKeeping:
    created: int
    last_seen: int
    changed: int

class Registry(Generic[K, V]):
    def __init__(self, config: Config):
        self.config = config
        self.entries: Dict[K, Tuple[BookKeeping, V]] = {}
        if self.config.is_active:
            self._load()

    def create_value(self, *args, **kwargs) -> V:
        raise NotImplementedError

    def update_value(self, value: V, timestamp: int, *args, **kwargs):
        raise NotImplementedError

    def add_or_update(self, key: K, timestamp: int, *args, **kwargs):
        if key not in self.entries:
            bk = BookKeeping(created=timestamp, last_seen=timestamp, changed=timestamp)
            val = self.create_value(*args, **kwargs)
            self.update_value(val, timestamp, *args, **kwargs)
            self.entries[key] = (bk, val)
        else:
            bk, val = self.entries[key]
            
            if timestamp < bk.created:
                bk.created = timestamp
            if timestamp > bk.last_seen:
                bk.last_seen = timestamp
                
            self.update_value(val, timestamp, *args, **kwargs)
            
            if timestamp > bk.changed:
                bk.changed = timestamp

    def get_serialization_version(self, value: V) -> int:
        return 1

    def serialize_key(self, key: K) -> str:
        return str(key)

    def deserialize_key(self, s: str) -> K:
        return s  # type: ignore

    def serialize_value(self, value: V) -> str:
        return str(value)

    def deserialize_value(self, s: str) -> V:
        return s  # type: ignore

    def _load(self):
        if not os.path.exists(self.config.filename):
            if self.config.allow_missing_file:
                return
            else:
                raise FileNotFoundError(f"Registry file missing: {self.config.filename}")
                
        with open(self.config.filename, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\n') for line in f]
            
        if len(lines) < 4:
            return
            
        header = lines[0]
        if header != "GKVR":
            raise ValueError("Invalid format: Missing GKVR header")
            
        # gkvr_version = int(lines[1])
        # content_version = int(lines[2])
        size = int(lines[3])
        
        idx = 4
        for _ in range(size):
            if idx >= len(lines):
                break
            key_str = lines[idx]
            idx += 1
            if idx >= len(lines):
                break
            
            # Tuple: BookKeeping, Value
            bk_created = int(lines[idx])
            idx += 1
            bk_last_seen = int(lines[idx])
            idx += 1
            bk_changed = int(lines[idx])
            idx += 1
            
            value_str = lines[idx]
            idx += 1
            
            key = self.deserialize_key(key_str)
            value = self.deserialize_value(value_str)
            bk = BookKeeping(created=bk_created, last_seen=bk_last_seen, changed=bk_changed)
            self.entries[key] = (bk, value)

    def save(self):
        if not self.config.is_active:
            return
            
        with open(self.config.filename, 'w', encoding='utf-8') as f:
            f.write("GKVR\n")
            f.write("1\n")
            
            if len(self.entries) > 0:
                first_val = next(iter(self.entries.values()))[1]
                content_version = self.get_serialization_version(first_val)
            else:
                content_version = 1
                
            f.write(f"{content_version}\n")
            f.write(f"{len(self.entries)}\n")
            
            for key, (bk, value) in self.entries.items():
                f.write(f"{self.serialize_key(key)}\n")
                f.write(f"{bk.created}\n")
                f.write(f"{bk.last_seen}\n")
                f.write(f"{bk.changed}\n")
                f.write(f"{self.serialize_value(value)}\n")

    def has(self, key: K) -> bool:
        return key in self.entries

    def get_all_entries(self) -> Dict[K, Tuple[BookKeeping, V]]:
        return self.entries
