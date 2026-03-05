from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Endurance:
    Current: int
    Max: int

    def Heal(self, Amount: int) -> None:
        if Amount <= 0:
            return
        self.Current = min(self.Max, self.Current + Amount)

    def TakeDamage(self, Amount: int) -> None:
        if Amount <= 0:
            return
        self.Current = max(0, self.Current - Amount)

    def ToDict(self) -> dict[str, int]:
        return {"Current": int(self.Current), "Max": int(self.Max)}

    @staticmethod
    def FromDict(Data: dict[str, Any]) -> Endurance:
        return Endurance(Current=int(Data["Current"]), Max=int(Data["Max"]))


@dataclass
class Inventory:
    Weapons: list[str] = field(default_factory=list)
    BackpackItems: list[str] = field(default_factory=list)
    SpecialItems: list[str] = field(default_factory=list)

    def AddWeapon(self, Name: str) -> bool:
        Clean = Name.strip()
        if not Clean:
            return False
        if Clean in self.Weapons:
            return False
        self.Weapons.append(Clean)
        return True

    def RemoveWeapon(self, Name: str) -> bool:
        Clean = Name.strip()
        if Clean in self.Weapons:
            self.Weapons.remove(Clean)
            return True
        return False

    def AddBackpackItem(self, Name: str) -> bool:
        Clean = Name.strip()
        if not Clean:
            return False
        # Backpack items can repeat (e.g., multiple Meals)
        self.BackpackItems.append(Clean)
        return True

    def RemoveBackpackItem(self, Name: str) -> bool:
        Clean = Name.strip()
        if Clean in self.BackpackItems:
            self.BackpackItems.remove(Clean)
            return True
        return False

    def AddSpecialItem(self, Name: str) -> bool:
        Clean = Name.strip()
        if not Clean:
            return False
        if Clean in self.SpecialItems:
            return False
        self.SpecialItems.append(Clean)
        return True

    def RemoveSpecialItem(self, Name: str) -> bool:
        Clean = Name.strip()
        if Clean in self.SpecialItems:
            self.SpecialItems.remove(Clean)
            return True
        return False

    def ToDict(self) -> dict[str, list[str]]:
        return {
            "Weapons": list(self.Weapons),
            "BackpackItems": list(self.BackpackItems),
            "SpecialItems": list(self.SpecialItems),
        }

    @staticmethod
    def FromDict(Data: dict[str, Any]) -> Inventory:
        return Inventory(
            Weapons=list(Data.get("Weapons", [])),
            BackpackItems=list(Data.get("BackpackItems", [])),
            SpecialItems=list(Data.get("SpecialItems", [])),
        )


@dataclass
class CharacterSheet:
    Name: str
    CombatSkill: int
    Endurance: Endurance

    KaiRank: str = "Initiate"
    KaiDisciplines: list[str] = field(default_factory=list)
    GoldCrowns: int = 0
    CurrentBook: int = 1
    Inventory: Inventory = field(default_factory=Inventory)

    def Heal(self, Amount: int) -> None:
        self.Endurance.Heal(Amount)

    def TakeDamage(self, Amount: int) -> None:
        self.Endurance.TakeDamage(Amount)

    def AddGold(self, Amount: int) -> None:
        if Amount <= 0:
            return
        self.GoldCrowns = self.GoldCrowns + Amount

    def SpendGold(self, Amount: int) -> bool:
        if Amount <= 0:
            return True
        if self.GoldCrowns < Amount:
            return False
        self.GoldCrowns -= Amount
        return True

    def AddDiscipline(self, DisciplineName: str) -> None:
        Clean = DisciplineName.strip()
        if not Clean:
            return
        if Clean not in self.KaiDisciplines:
            self.KaiDisciplines.append(Clean)

    def RemoveDiscipline(self, DisciplineName: str) -> None:
        Clean = DisciplineName.strip()
        if Clean in self.KaiDisciplines:
            self.KaiDisciplines.remove(Clean)

    def ToDict(self) -> dict[str, Any]:
        return {
            "SchemaVersion": 1,
            "Game": {
                "Series": "Lone Wolf",
                "SupportedBooks": [1, 2, 3, 4, 5],
                "CurrentBook": int(self.CurrentBook),
            },
            "Character": {
                "Name": self.Name,
                "KaiRank": self.KaiRank,
                "KaiDisciplines": list(self.KaiDisciplines),
                "CombatSkill": int(self.CombatSkill),
                "Endurance": self.Endurance.ToDict(),
                "GoldCrowns": int(self.GoldCrowns),
            },
            "Inventory": self.Inventory.ToDict(),
        }

    @staticmethod
    def FromDict(Data: dict[str, Any]) -> CharacterSheet:
        CharacterData = Data.get("Character", {})
        GameData = Data.get("Game", {})
        InventoryData = Data.get("Inventory", {})

        return CharacterSheet(
            Name=str(CharacterData["Name"]),
            KaiRank=str(CharacterData.get("KaiRank", "Initiate")),
            KaiDisciplines=list(CharacterData.get("KaiDisciplines", [])),
            CombatSkill=int(CharacterData["CombatSkill"]),
            Endurance=Endurance.FromDict(CharacterData["Endurance"]),
            GoldCrowns=int(CharacterData.get("GoldCrowns", 0)),
            CurrentBook=int(GameData.get("CurrentBook", 1)),
            Inventory=Inventory.FromDict(InventoryData),
        )