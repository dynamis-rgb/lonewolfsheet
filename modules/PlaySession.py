from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path

from modules.AppConfig import LoadInventoryRules
from modules.DomainModels import CharacterSheet, Endurance
from modules.JsonRepository import JsonRepository
from modules.RuleBooks1to5 import CombatResultsTable, RuleBooks1to5


@dataclass
class FightState:
    EnemyCombatSkill: int
    EnemyEndurance: Endurance


@dataclass(frozen=True)
class TemporaryCombatModifier:
    Source: str
    CombatSkillBonus: int
    RemainingRounds: int | None = None  # None means until this fight ends.


@dataclass
class PlaySession:
    Repo: JsonRepository
    SavePath: Path
    Sheet: CharacterSheet
    CtrTable: CombatResultsTable
    Fight: FightState | None = None
    Rng: random.Random = field(default_factory=random.Random)
    Rules: RuleBooks1to5 = field(default_factory=lambda: RuleBooks1to5(LoadInventoryRules()))
    TemporaryModifiers: list[TemporaryCombatModifier] = field(default_factory=list)
    MindblastEnabled: bool = False

    def AddTemporaryCombatModifier(
        self, Source: str, CombatSkillBonus: int, Rounds: int | None = None
    ) -> TemporaryCombatModifier:
        """Stack an effect for this fight, or for the next Rounds applied rounds."""
        if self.Fight is None:
            raise ValueError("No active fight.")
        if not isinstance(Source, str) or not Source.strip():
            raise ValueError("Modifier source must be a nonempty string.")
        if isinstance(CombatSkillBonus, bool) or not isinstance(CombatSkillBonus, int):
            raise TypeError("CombatSkillBonus must be an integer.")
        if Rounds is not None:
            if isinstance(Rounds, bool) or not isinstance(Rounds, int):
                raise TypeError("Rounds must be an integer or None.")
            if Rounds <= 0:
                raise ValueError("Rounds must be greater than zero.")
        Modifier = TemporaryCombatModifier(Source.strip(), CombatSkillBonus, Rounds)
        self.TemporaryModifiers.append(Modifier)
        return Modifier

    def RemoveTemporaryCombatModifiers(self, Source: str) -> int:
        """Remove every stacked effect from the named source."""
        Before = len(self.TemporaryModifiers)
        self.TemporaryModifiers[:] = [
            Modifier for Modifier in self.TemporaryModifiers
            if Modifier.Source.casefold() != Source.strip().casefold()
        ]
        return Before - len(self.TemporaryModifiers)

    def ClearTemporaryCombatModifiers(self) -> None:
        self.TemporaryModifiers.clear()
        self.MindblastEnabled = False

    def SetMindblast(self, Enabled: bool) -> None:
        if not isinstance(Enabled, bool):
            raise TypeError("Enabled must be a boolean.")
        if Enabled:
            if self.Fight is None:
                raise ValueError("No active fight.")
            if not any(Name.strip().casefold() == "mindblast" for Name in self.Sheet.KaiDisciplines):
                raise ValueError("Mindblast discipline is required.")
        self.MindblastEnabled = Enabled

    def GetTemporaryCombatSkillBonus(self) -> int:
        if self.Fight is None:
            return 0
        MindblastKnown = any(
            Name.strip().casefold() == "mindblast" for Name in self.Sheet.KaiDisciplines
        )
        return sum(Modifier.CombatSkillBonus for Modifier in self.TemporaryModifiers) + (
            2 if self.MindblastEnabled and MindblastKnown else 0
        )

    def UseCombatPotion(self, Name: str) -> TemporaryCombatModifier:
        """Consume one catalog potion for its CS bonus for the current fight.

        Healing and temporary maximum-endurance effects require separate handling.
        Effects live only in this session; the consumed inventory item is saved.
        """
        if self.Fight is None:
            raise ValueError("No active fight.")
        Item = self.Rules.GetItemDefinition(Name)
        if (Item is None or not Item.IsConsumable or not Item.CombatSkillBonus
                or Item.EnduranceBonus or Item.RestoresEndurance):
            raise ValueError("Item must be a catalog consumable with only a combat skill effect.")
        Inventory = self.Sheet.Inventory
        if Item.Category == "backpack":
            Owned, Remove = Inventory.BackpackItems, Inventory.RemoveBackpackItem
        elif Item.Category == "special":
            Owned, Remove = Inventory.SpecialItems, Inventory.RemoveSpecialItem
        else:
            raise ValueError("Combat potion must be a backpack or special item.")
        OwnedName = next(
            (Other for Other in Owned if Other.strip().casefold() == Name.strip().casefold()), None
        )
        if OwnedName is None:
            raise ValueError(f"Item is not owned: {Name}")
        CanonicalName = self.Rules.ResolveItem(Name).Name
        Modifier = self.AddTemporaryCombatModifier(CanonicalName, Item.CombatSkillBonus)
        Remove(OwnedName)
        self.Save()
        return Modifier

    def _AdvanceTemporaryModifiers(self) -> None:
        self.TemporaryModifiers[:] = [
            TemporaryCombatModifier(
                Modifier.Source, Modifier.CombatSkillBonus, Modifier.RemainingRounds - 1
            ) if Modifier.RemainingRounds is not None else Modifier
            for Modifier in self.TemporaryModifiers
            if Modifier.RemainingRounds is None or Modifier.RemainingRounds > 1
        ]

    @staticmethod
    def CreateOrLoad(Repo: JsonRepository, SavePath: Path) -> PlaySession:
        LocalCtrTablePath = Path("configs") / "CombatResultsTable_local.json"

        if not LocalCtrTablePath.exists():
            raise FileNotFoundError(
                "Missing configs/CombatResultsTable_local.json. "
                "Create it from the template and fill in your combat table."
            )

        CtrTable = CombatResultsTable.LoadFromJson(LocalCtrTablePath)

        if not SavePath.exists():
            raise FileNotFoundError(f"Save file not found: {SavePath}")

        Sheet = Repo.LoadCharacter(SavePath)
        return PlaySession(
            Repo=Repo,
            SavePath=SavePath,
            Sheet=Sheet,
            CtrTable=CtrTable,
        )

    def Save(self) -> None:
        self.Repo.SaveCharacter(self.Sheet, self.SavePath)

    def RollRandomNumber(self) -> int:
        return self.Rng.randint(0, 9)

    def GetEffectiveCombatSkill(self) -> int:
        Modifiers = self.Rules.ResolveCombatModifiers(self.Sheet)
        return (self.Sheet.CombatSkill + Modifiers.CombatSkillBonus
                + self.GetTemporaryCombatSkillBonus())

    def GetCombatRatio(self) -> int:
        if self.Fight is None:
            raise ValueError("No active fight.")
        return self.GetEffectiveCombatSkill() - self.Fight.EnemyCombatSkill

    def StartFight(self, EnemyCombatSkill: int, EnemyEndurancePoints: int) -> str:
        self.ClearTemporaryCombatModifiers()
        self.Fight = FightState(
            EnemyCombatSkill=int(EnemyCombatSkill),
            EnemyEndurance=Endurance(
                Current=int(EnemyEndurancePoints),
                Max=int(EnemyEndurancePoints),
            ),
        )

        Ratio = self.GetCombatRatio()

        return (
            f"Fight Started.\n"
            f"Your CS: {self.GetEffectiveCombatSkill()} | "
            f"Enemy CS: {self.Fight.EnemyCombatSkill} | "
            f"Combat Ratio: {Ratio}\n"
            f"Enemy EP: {self.Fight.EnemyEndurance.Current}/{self.Fight.EnemyEndurance.Max}"
        )

    def ApplyFightRound(self, YourDamage: int, EnemyDamage: int) -> str:
        if self.Fight is None:
            return "No active fight. Start one with: fight <enemyCS> <enemyEP>"

        BeforeYou = self.Sheet.Endurance.Current
        BeforeEnemy = self.Fight.EnemyEndurance.Current

        self.Sheet.TakeDamage(int(YourDamage))
        self.Fight.EnemyEndurance.TakeDamage(int(EnemyDamage))

        AfterYou = self.Sheet.Endurance.Current
        AfterEnemy = self.Fight.EnemyEndurance.Current
        self._AdvanceTemporaryModifiers()

        OutcomeLines = [
            f"Round applied. You: {BeforeYou} -> {AfterYou} | "
            f"Enemy: {BeforeEnemy} -> {AfterEnemy}"
        ]

        if AfterEnemy == 0:
            OutcomeLines.append("Enemy Defeated.")
            self.Fight = None

        if AfterYou == 0:
            OutcomeLines.append("You are at 0 endurance. Your life and adventure end here!")
            self.Fight = None

        if self.Fight is None:
            self.ClearTemporaryCombatModifiers()

        self.Save()
        return "\n".join(OutcomeLines)

    def ResolveAutomaticRound(self) -> str:
        if self.Fight is None:
            return "No active fight. Start one with: fight <enemyCS> <enemyEP>"

        Ratio = self.GetCombatRatio()
        Roll = self.RollRandomNumber()
        Outcome = self.CtrTable.ResolveRound(Ratio, Roll)

        ResultText = self.ApplyFightRound(Outcome.YouDamage, Outcome.EnemyDamage)

        return (
            f"Combat Ratio: {Ratio}\n"
            f"Random Number: {Roll}\n"
            f"CRT Result: You take {Outcome.YouDamage}, "
            f"Enemy takes {Outcome.EnemyDamage}\n"
            f"{ResultText}"
        )

    def StatusText(self) -> str:
        Lines: list[str] = []
        Lines.append(f"Name: {self.Sheet.Name}")
        Lines.append(f"Book: {self.Sheet.CurrentBook}")
        Lines.append(f"Section: {self.Sheet.CurrentSection}")
        Lines.append(f"CS: {self.Sheet.CombatSkill}")
        Lines.append(f"Effective CS: {self.GetEffectiveCombatSkill()}")
        if self.Fight is not None:
            Lines.append(f"Temporary CS bonus: {self.GetTemporaryCombatSkillBonus():+d}")
            Lines.append(f"Mindblast: {'on' if self.MindblastEnabled else 'off'}")
            for Modifier in self.TemporaryModifiers:
                Duration = (
                    "this fight" if Modifier.RemainingRounds is None
                    else f"{Modifier.RemainingRounds} round(s)"
                )
                Lines.append(f"  {Modifier.Source}: {Modifier.CombatSkillBonus:+d} CS ({Duration})")
        Lines.append(f"EP: {self.Sheet.Endurance.Current}/{self.Sheet.Endurance.Max}")
        Lines.append(f"Gold: {self.Sheet.GoldCrowns}")
        Lines.append(
            f"Disciplines: "
            f"{', '.join(self.Sheet.KaiDisciplines) if self.Sheet.KaiDisciplines else '(none)'}"
        )
        Lines.append(
            f"Weapons: "
            f"{', '.join(self.Sheet.Inventory.Weapons) if self.Sheet.Inventory.Weapons else '(none)'}"
        )
        Lines.append(
            f"Backpack: "
            f"{', '.join(self.Sheet.Inventory.BackpackItems) if self.Sheet.Inventory.BackpackItems else '(none)'}"
        )
        Lines.append(
            f"Special: "
            f"{', '.join(self.Sheet.Inventory.SpecialItems) if self.Sheet.Inventory.SpecialItems else '(none)'}"
        )

        if self.Fight is not None:
            Lines.append(
                f"Active Fight: Enemy CS {self.Fight.EnemyCombatSkill} | "
                f"Enemy EP {self.Fight.EnemyEndurance.Current}/{self.Fight.EnemyEndurance.Max} | "
                f"Ratio {self.GetCombatRatio()}"
            )

        return "\n".join(Lines)
