from dataclasses import dataclass

@dataclass
class Config:
    is_active: bool
    allow_missing_file: bool
    filename: str
    must_expire_keys: bool
    expiration_period_days: int
