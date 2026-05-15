from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path

from modules.DomainModels import CharacterSheet, Endurance
from modules.JsonRepository import JsonRepository
from modules.RuleBooks1to5 import CombatResultsTable


@dataclass
class FightState:
    EnemyCombatSkill: int
    EnemyEndurance: Endurance


@dataclass
class PlaySession:
    Repo: JsonRepository
    SavePath: Path
    Sheet: CharacterSheet
    CtrTable: CombatResultsTable
    Fight: FightState | None = None
    Rng: random.Random = field(default_factory=random.Random)

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

    def GetCombatRatio(self) -> int:
        if self.Fight is None:
            raise ValueError("No active fight.")
        return self.Sheet.CombatSkill - self.Fight.EnemyCombatSkill

    def StartFight(self, EnemyCombatSkill: int, EnemyEndurancePoints: int) -> str:
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
            f"Your CS: {self.Sheet.CombatSkill} | "
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

        OutcomeLines = [
            f"Round applied. You: {BeforeYou} -> {AfterYou} | "
            f"Enemy: {BeforeEnemy} -> {AfterEnemy}"
        ]

        if AfterEnemy == 0:
            OutcomeLines.append("Enemy Defeated.")
            self.Fight = None

        if AfterYou == 0:
            OutcomeLines.append("You are at 0 endurance. Your life and adventure end here!")

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
