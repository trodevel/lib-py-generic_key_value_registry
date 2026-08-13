from enum import Enum, auto


class UpdateStatus(Enum):
    ADDED = auto()
    EXISTING_UPDATED = auto()
    EXISTING_NOT_UPDATED = auto()
