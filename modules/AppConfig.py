from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any
from types import MappingProxyType
from typing import Literal, Mapping

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


@dataclass(frozen=True)
class ItemDefinition:
    Category: Literal["backpack", "special", "weapon"]
    SlotCost: int
    IsWeapon: bool
    IsConsumable: bool
    CombatSkillBonus: int
    EnduranceBonus: int
    WeaponTypes: tuple[str, ...]
    RestoresEndurance: int


@dataclass(frozen=True)
class DisciplineDefinition:
    Description: str
    AvailableBooks: tuple[int, ...]


def LoadDisciplineCatalog() -> Mapping[str, DisciplineDefinition]:
    """Load validated, immutable definitions keyed by canonical discipline name."""
    config_path = Path(__file__).resolve().parent.parent / "configs" / "defaultRules.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    disciplines = data["Disciplines"]
    if not isinstance(disciplines, dict):
        raise TypeError("Disciplines must be an object keyed by discipline name.")

    catalog: dict[str, DisciplineDefinition] = {}
    seen: set[str] = set()
    for name, raw in disciplines.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Discipline names must be nonempty strings.")
        normalized = name.strip().casefold()
        if normalized in seen:
            raise ValueError(f"Duplicate discipline name: {name!r}")
        seen.add(normalized)
        if not isinstance(raw, dict):
            raise TypeError(f"Disciplines.{name} must be an object.")
        description = raw["Description"]
        if not isinstance(description, str):
            raise TypeError(f"Disciplines.{name}.Description must be a string.")
        books = raw["AvailableBooks"]
        if not isinstance(books, list):
            raise TypeError(f"Disciplines.{name}.AvailableBooks must be a list.")
        for book in books:
            validate_nonnegative_int(book, f"Disciplines.{name}.AvailableBooks")
            if book == 0:
                raise ValueError(f"Disciplines.{name}.AvailableBooks must contain positive book numbers.")
        if len(books) != len(set(books)):
            raise ValueError(f"Disciplines.{name}.AvailableBooks must not contain duplicates.")
        catalog[name] = DisciplineDefinition(
            Description=description, AvailableBooks=tuple(books)
        )
    return MappingProxyType(catalog)


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


def LoadItemCatalog() -> Mapping[str, ItemDefinition]:
    """Load a read-only catalog keyed by the item names used in saved inventories.

    All JSON access and validation stays here; callers use ItemDefinition attributes.
    """
    config_path = Path(__file__).resolve().parent.parent / "configs" / "defaultRules.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    items = data["Items"]
    if not isinstance(items, dict):
        raise TypeError("Items must be an object keyed by item name.")

    catalog = {}
    for name, raw in items.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Item names must be nonempty strings.")
        if not isinstance(raw, dict):
            raise TypeError(f"Items.{name} must be an object.")

        category = raw["Category"]
        if category not in ("backpack", "special", "weapon"):
            raise ValueError(f"Items.{name}.Category must be backpack, special, or weapon.")
        for field in ("IsWeapon", "IsConsumable"):
            if not isinstance(raw[field], bool):
                raise TypeError(f"Items.{name}.{field} must be a boolean.")
        for field in ("CombatSkillBonus", "EnduranceBonus"):
            if isinstance(raw[field], bool) or not isinstance(raw[field], int):
                raise TypeError(f"Items.{name}.{field} must be an integer.")

        weapon_types = raw.get("WeaponTypes", [])
        if not isinstance(weapon_types, list) or any(
            not isinstance(value, str) or not value.strip() for value in weapon_types
        ):
            raise TypeError(f"Items.{name}.WeaponTypes must be a list of nonempty strings.")

        catalog[name] = ItemDefinition(
            Category=category,
            SlotCost=validate_nonnegative_int(raw["SlotCost"], f"Items.{name}.SlotCost"),
            IsWeapon=raw["IsWeapon"],
            IsConsumable=raw["IsConsumable"],
            CombatSkillBonus=raw["CombatSkillBonus"],
            EnduranceBonus=raw["EnduranceBonus"],
            WeaponTypes=tuple(weapon_types),
            RestoresEndurance=validate_nonnegative_int(
                raw.get("RestoresEndurance", 0), f"Items.{name}.RestoresEndurance"
            ),
        )
    return MappingProxyType(catalog)
