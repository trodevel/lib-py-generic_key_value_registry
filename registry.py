import os
from typing import TypeVar, Generic, Dict, Tuple
from dataclasses import dataclass

K = TypeVar('K')
V = TypeVar('V')

try:
    from .registry_config import Config
    from .registry_book_keeping import BookKeeping
    from .update_status import UpdateStatus
except ImportError:
    from registry_config import Config
    from registry_book_keeping import BookKeeping
    from update_status import UpdateStatus

class Registry(Generic[K, V]):
    def __init__(self, config: Config):
        self.config = config
        self.entries: Dict[K, Tuple[BookKeeping, V]] = {}
        if self.config.is_active:
            self._load()

    def _update_value(self, value: V, new_value: V) -> bool:
        raise NotImplementedError

    def add_or_update_ts(self, key: K, value: V, timestamp: int) -> UpdateStatus:
        if key not in self.entries:
            bk = BookKeeping(created=timestamp, last_seen=timestamp, changed=timestamp)
            self.entries[key] = (bk, value)
            return UpdateStatus.ADDED
        else:
            bk, val = self.entries[key]

            if timestamp < bk.created:
                bk.created = timestamp
            if timestamp > bk.last_seen:
                bk.last_seen = timestamp

            if self._update_value(val, value):
                if timestamp > bk.changed:
                    bk.changed = timestamp
                return UpdateStatus.EXISTING_UPDATED
            else:
                return UpdateStatus.EXISTING_NOT_UPDATED


    def get_serialization_version(self, value: V) -> int:
        return 1

    def serialize_key(self, key: K) -> str:
        return str(key)

    def deserialize_key(self, s: str) -> K:
        return s  # type: ignore

    def serialize_value(self, value: V) -> str:
        return str(value)

    def deserialize_value(self, version: int, s: str) -> V:
        """Converts string representation back to value object for a given content serialization version."""
        return s  # type: ignore

    def serialize_bookkeeping(self, bk: BookKeeping) -> str:
        return f"{bk.created} {bk.last_seen} {bk.changed}"

    def deserialize_bookkeeping(self, s: str) -> BookKeeping:
        parts = s.split(' ')
        return BookKeeping(created=int(parts[0]), last_seen=int(parts[1]), changed=int(parts[2]))

    def _load_header(self, lines: list[str]) -> Tuple[int, int, int]:
        if len(lines) < 4:
            return 0, 0, 0

        header = lines[0]
        if header != "GKVR":
            raise ValueError("Invalid format: Missing GKVR header")

        # gkvr_version = int(lines[1])
        content_version = int(lines[2])
        size = int(lines[3])
        return 4, content_version, size

    def _load_content(self, lines: list[str], start_idx: int, content_version: int, size: int):
        idx = start_idx
        for _ in range(size):
            if idx >= len(lines):
                break
            line = lines[idx]
            idx += 1

            parts = line.split(' ', 4)
            if len(parts) < 4:
                continue

            key_str = parts[0]
            bk_str = f"{parts[1]} {parts[2]} {parts[3]}"
            value_str = parts[4] if len(parts) > 4 else ""

            key = self.deserialize_key(key_str)
            value = self.deserialize_value(content_version, value_str)
            bk = self.deserialize_bookkeeping(bk_str)
            self.entries[key] = (bk, value)

    def _load(self):
        if not os.path.exists(self.config.filename):
            if self.config.allow_missing_file:
                return
            else:
                raise FileNotFoundError(f"Registry file missing: {self.config.filename}")

        with open(self.config.filename, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\n') for line in f]

        start_idx, content_version, size = self._load_header(lines)
        if size > 0:
            self._load_content(lines, start_idx, content_version, size)
    def _save_header(self, f):
        f.write("GKVR\n")
        f.write("1\n")

        if len(self.entries) > 0:
            first_val = next(iter(self.entries.values()))[1]
            content_version = self.get_serialization_version(first_val)
        else:
            content_version = 1

        f.write(f"{content_version}\n")
        f.write(f"{len(self.entries)}\n")

    def _save_content(self, f):
        for key, (bk, value) in self.entries.items():
            f.write(f"{self.serialize_key(key)} {self.serialize_bookkeeping(bk)} {self.serialize_value(value)}\n")

    def save(self):
        if not self.config.is_active:
            return

        with open(self.config.filename, 'w', encoding='utf-8') as f:
            self._save_header(f)
            self._save_content(f)

    def has(self, key: K) -> bool:
        return key in self.entries

    def get(self, key: K) -> V:
        if key not in self.entries:
            raise KeyError(f"Key '{key}' not found in registry")
        return self.entries[key][1]

    def delete(self, key: K):
        if key in self.entries:
            del self.entries[key]

    def expire_keys(self, current_timestamp: int):
        if not self.config.must_expire_keys:
            return

        expiration_secs = self.config.expiration_period_days * 86400
        threshold = current_timestamp - expiration_secs

        keys_to_delete = [
            key for key, (bk, value) in self.entries.items()
            if bk.last_seen < threshold
        ]

        for key in keys_to_delete:
            self.delete(key)

    def get_all_entries(self) -> Dict[K, Tuple[BookKeeping, V]]:
        return self.entries
