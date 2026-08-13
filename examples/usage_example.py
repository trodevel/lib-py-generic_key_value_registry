import sys
from pathlib import Path

# Add package root path so generic_key_value_registry is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from generic_key_value_registry import Config
from contact_registry import ContactRegistry


def main():
    data_file = Path(__file__).parent / "example_registry.dat"

    # Clean up old file if present
    if data_file.exists():
        data_file.unlink()

    # Define configuration
    config = Config(
        is_active=True,
        allow_missing_file=True,
        filename=str(data_file),
        must_expire_keys=True,
        expiration_period_days=30,
    )

    print("--- 1. Initialize Registry ---")
    registry = ContactRegistry(config)
    print(f"Initial registry entries count: {len(registry.get_all_entries())}")

    print("\n--- 2. Add and Update Entries ---")
    t1 = 1700000000
    t2 = 1700003600

    registry.add_or_update_ts(
        "user_1", timestamp=t1, first_name="Alice", last_name="Smith", age=30
    )
    registry.add_or_update_ts(
        "user_2", timestamp=t1, first_name="Bob", last_name="Jones", age=25
    )
    # Update user_1 age at t2
    registry.add_or_update_ts("user_1", timestamp=t2, age=31)

    print(f"Has 'user_1': {registry.has('user_1')}")
    print(f"'user_1' contact details: {registry.get('user_1')}")

    print("\n--- 3. Save to Disk ---")
    registry.save()
    print(f"Saved to '{data_file}'")

    print("\n--- 4. File Contents on Disk ---")
    with open(data_file, "r", encoding="utf-8") as f:
        print(f.read())

    print("--- 5. Load from Disk ---")
    loaded_registry = ContactRegistry(config)
    print(f"Loaded registry entries count: {len(loaded_registry.get_all_entries())}")
    for key, (bk, value) in loaded_registry.get_all_entries().items():
        print(f"Key: '{key}', Metadata: {bk}, Contact: {value}")

    # Cleanup generated file
    if data_file.exists():
        data_file.unlink()


if __name__ == "__main__":
    main()
