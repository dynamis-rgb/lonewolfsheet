from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any

@dataclass(frozen=True)
class AppConfig:
    SaveDirectory: Path

def LoadAppConfig() -> AppConfig:
    ConfigPath = Path("configs") / "appsettings.json"
    DefaultSaveDirectory = Path("sample_data")

    if not ConfigPath.exists():
        return AppConfig(SaveDirectory=DefaultSaveDirectory)

    Data = json.loads(ConfigPath.read_text(encoding="utf-8"))
    RawSaveDirectory = str(Data.get("SaveDirectory", "")).strip()
    if not RawSaveDirectory:
        return AppConfig(SaveDirectory=DefaultSaveDirectory)

    return AppConfig(SaveDirectory=Path(RawSaveDirectory))


@dataclass(frozen=True)
class InventoryRules:
    MaxBackpackItems: int
    MaxSpecialItems: int


def validate_nonnegative_int(value: Any, field_name: str) -> int:
    # bool is a subclass of int in Python, so reject it explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer.")

    if value < 0:
        raise ValueError(f"{field_name} must be equal to or greater than zero.")

    return value


def LoadInventoryRules() -> InventoryRules:
    project_folder = Path(__file__).resolve().parent.parent
    config_path = project_folder / "configs" / "defaultRules.json"

    data = json.loads(config_path.read_text(encoding="utf-8"))

    inventory_limits = data["InventoryLimits"]

    max_backpack_items = validate_nonnegative_int(
        inventory_limits["MaxBackpackItems"],
        "MaxBackpackItems",
    )

    max_special_items = validate_nonnegative_int(
        inventory_limits["MaxSpecialItems"],
        "MaxSpecialItems",
    )

    return InventoryRules(
        MaxBackpackItems=max_backpack_items,
        MaxSpecialItems=max_special_items,
    )