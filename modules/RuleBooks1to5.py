from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Literal, Mapping

from modules.AppConfig import InventoryRules, ItemDefinition, LoadItemCatalog
from modules.DomainModels import CharacterSheet


@dataclass(frozen=True)
class InventoryCheckResult:
    Allowed: bool
    Reason: str = ""


@dataclass(frozen=True)
class ItemResolutionResult:
    Status: Literal["found", "not_found", "ambiguous"]
    Name: str | None = None
    Definition: ItemDefinition | None = None
    Candidates: tuple[str, ...] = ()


class RuleBooks1to5:
    def __init__(
        self,
        InventoryRules: InventoryRules,
        ItemCatalog: Mapping[str, ItemDefinition] | None = None,
    ) -> None:
        self.InventoryRules = InventoryRules
        self.ItemCatalog = MappingProxyType(
            dict(LoadItemCatalog() if ItemCatalog is None else ItemCatalog)
        )
        self._ItemNames: dict[str, str] = {}
        for Name in self.ItemCatalog:
            Normalized = Name.strip().casefold()
            if not Normalized or Normalized in self._ItemNames:
                raise ValueError(f"Item catalog contains a blank or duplicate item name: {Name!r}")
            self._ItemNames[Normalized] = Name

    def GetItemDefinition(self, Name: str) -> ItemDefinition | None:
        """Look up a full item name, ignoring case and surrounding whitespace."""
        CanonicalName = self._ItemNames.get(Name.strip().casefold())
        return self.ItemCatalog[CanonicalName] if CanonicalName is not None else None

    def ResolveItem(self, Query: str) -> ItemResolutionResult:
        """Resolve exact names first, then prefixes, then substrings.

        An ambiguous prefix returns its candidates without trying substring matching.
        Returned names always retain the catalog's canonical spelling.
        """
        Normalized = Query.strip().casefold()
        if not Normalized:
            return ItemResolutionResult(Status="not_found")

        Exact = self._ItemNames.get(Normalized)
        if Exact is not None:
            return ItemResolutionResult(
                Status="found", Name=Exact, Definition=self.ItemCatalog[Exact]
            )

        Candidates = [
            Name for Key, Name in self._ItemNames.items() if Key.startswith(Normalized)
        ]
        if not Candidates:
            Candidates = [
                Name for Key, Name in self._ItemNames.items() if Normalized in Key
            ]
        if len(Candidates) == 1:
            Name = Candidates[0]
            return ItemResolutionResult(
                Status="found", Name=Name, Definition=self.ItemCatalog[Name]
            )
        if Candidates:
            return ItemResolutionResult(
                Status="ambiguous", Candidates=tuple(sorted(Candidates, key=str.casefold))
            )
        return ItemResolutionResult(Status="not_found")
    
    def _SlotCount(self, Names: list[str]) -> int:
        # Legacy custom items still occupy one slot until cataloged.
        return sum(
            Item.SlotCost if (Item := self.GetItemDefinition(Name)) is not None else 1
            for Name in Names
        )

    def CanAddItem(self, Sheet: CharacterSheet, Name: str, Category: str) -> InventoryCheckResult:
        Item = self.GetItemDefinition(Name)
        if Item is None:
            return InventoryCheckResult(False, f"Unknown catalog item: {Name}")
        if Item.Category != Category:
            return InventoryCheckResult(
                False, f"{Name} is a {Item.Category} item; use add-{Item.Category}."
            )
        if Category == "weapon":
            if not Item.IsWeapon:
                return InventoryCheckResult(False, f"{Name} is not a weapon.")
            Owned = Sheet.Inventory.Weapons
        elif Category == "special":
            Owned = Sheet.Inventory.SpecialItems
        else:
            Owned = Sheet.Inventory.BackpackItems
        if Category != "backpack" and any(
            Existing.strip().casefold() == Name.strip().casefold() for Existing in Owned
        ):
            return InventoryCheckResult(False, f"{Name} is already present.")
        if Category == "backpack":
            return self.CanAddBackpackItem(Sheet, Name)
        if Category == "special":
            return self.CanAddSpecialItem(Sheet, Name)
        # No weapon-count limit is defined in InventoryRules.
        return InventoryCheckResult(True)

    def CanAddBackpackItem(
        self, Sheet: CharacterSheet, Name: str | None = None
    ) -> InventoryCheckResult:
        Item = self.GetItemDefinition(Name) if Name is not None else None
        if Name is not None and (Item is None or Item.Category != "backpack"):
            return InventoryCheckResult(False, f"Not a catalog backpack item: {Name}")
        SlotCost = Item.SlotCost if Item is not None else 1
        CurrentCount = self._SlotCount(Sheet.Inventory.BackpackItems)
        MaxCount = self.InventoryRules.MaxBackpackItems

        if CurrentCount + SlotCost > MaxCount:
            return InventoryCheckResult(
                Allowed=False,
                Reason=(f"Backpack is full ({CurrentCount}/{MaxCount})." if CurrentCount >= MaxCount
                        else f"Not enough backpack slots ({CurrentCount}/{MaxCount}; needs {SlotCost}).")
            )
        
        return InventoryCheckResult(Allowed=True)
    
    def CanAddSpecialItem(
        self, Sheet: CharacterSheet, Name: str | None = None
    ) -> InventoryCheckResult:
        Item = self.GetItemDefinition(Name) if Name is not None else None
        if Name is not None and (Item is None or Item.Category != "special"):
            return InventoryCheckResult(False, f"Not a catalog special item: {Name}")
        SlotCost = Item.SlotCost if Item is not None else 1
        CurrentCount = self._SlotCount(Sheet.Inventory.SpecialItems)
        MaxCount = self.InventoryRules.MaxSpecialItems

        if CurrentCount + SlotCost > MaxCount:
            return InventoryCheckResult(
                Allowed=False,
                Reason=f"Not enough special item slots ({CurrentCount}/{MaxCount}; needs {SlotCost})."
            )
        
        return InventoryCheckResult(Allowed=True)
    
    def ValidateInventory(self, Sheet: CharacterSheet) -> list[str]:
        Errors: list[str] = []

        BackpackCount = self._SlotCount(Sheet.Inventory.BackpackItems)
        MaxBackpackCount = self.InventoryRules.MaxBackpackItems
        if BackpackCount > MaxBackpackCount:
            Errors.append(
                f"Backpack item limit exceeded ({BackpackCount}/{MaxBackpackCount})."
            )
        
        SpecialCount = self._SlotCount(Sheet.Inventory.SpecialItems)
        MaxSpecialCount = self.InventoryRules.MaxSpecialItems
        if SpecialCount > MaxSpecialCount:
            Errors.append(
                f"Special item limit exceeded ({SpecialCount}/{MaxSpecialCount})."
            )
        return Errors
    
    

@dataclass(frozen=True)
class CombatOutcome:
    YouDamage: int
    EnemyDamage: int


class CombatResultsTable:

    def __init__(self, MinRatio: int, MaxRatio: int, Rows: dict[int, list[list[int]]]) -> None:
        self.MinRatio = MinRatio
        self.MaxRatio = MaxRatio
        self.Rows = Rows

    @staticmethod
    def LoadFromJson(FilePath: Path) -> "CombatResultsTable":
        Data = json.loads(FilePath.read_text(encoding="utf-8"))

        Rows = {int(Key): list(Value) for Key, Value in Data["Rows"].items()}

        return CombatResultsTable(
            MinRatio=int(Data["MinRatio"]),
            MaxRatio=int(Data["MaxRatio"]),
            Rows=Rows,
        )

    def ResolveRound(self, CombatRatio: int, RandomNumber: int) -> CombatOutcome:

        if RandomNumber < 0 or RandomNumber > 9:
            raise ValueError("RandomNumber must be between 0 and 9")

        Ratio = max(self.MinRatio, min(self.MaxRatio, int(CombatRatio)))

        Row = self.Rows.get(Ratio)

        if Row is None:
            raise ValueError(f"No CRT row found for ratio {Ratio}")

        if len(Row) != 10:
            raise ValueError(f"CRT row for ratio {Ratio} must have 10 entries")

        Cell = Row[RandomNumber]

        if not isinstance(Cell, list) or len(Cell) != 2:
            raise ValueError(f"Invalid CRT cell at ratio {Ratio}, roll {RandomNumber}")

        return CombatOutcome(
            EnemyDamage=int(Cell[0]),
            YouDamage=int(Cell[1]),
        )
