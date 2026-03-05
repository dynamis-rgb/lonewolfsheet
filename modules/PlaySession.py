from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

from modules.DomainModels import CharacterSheet, Endurance
from modules.JsonRepository import JsonRepository

@dataclass
class FightState:
    EnemyCombatSkill: int
    EnemyEndurance: Endurance

@dataclass
class PlaySession:
    Repo: JsonRepository
    SavePath: Path
    Sheet: CharacterSheet
    Fight: FightState | None = None
    Rng: random.Random = random.Random()

    @staticmethod
    def CreateOrLoad(Repo: JsonRepository, SavePath: Path) -> PlaySession:
        if SavePath.exists():
            Sheet=Repo.LoadCharacter(SavePath)
            return PlaySession(Repo=Repo, SavePath=SavePath, Sheet=Sheet)
        
        Sheet=CharacterSheet(
            Name="Lone Wolf",
            CombatSkill=17,
            Endurance=Endurance(Current=22, Max=22),
            KaiDisciplines=["Camouflage","Hunting", "Sixth Sense", "Healing", "Tracking"],
            GoldCrowns=12,
            CurrentBook=1,
        )

        Repo.SaveCharacter(Sheet,SavePath)
        return PlaySession(Repo=Repo, SavePath=SavePath, Sheet=Sheet)
    
    def Save(self) -> None:
        self.Repo.SaveCharacter(self.Sheet, self.SavePath)
    
    def RollRandomNumber(self) -> int:
        return self.Rng.randint(0,9)
    
    def StartFight(self, EnemyCombatSkill: int, EnemyEndurancePoints: int) -> str:
        self.Fight = FightState(
            EnemyCombatSkill=int(EnemyCombatSkill),
            EnemyEndurance=Endurance(Current=int(EnemyEndurancePoints), Max=int(EnemyEndurancePoints)),
        )
        Ratio=self.Sheet.CombatSkill - self.Fight.EnemyCombatSkill
        return (
            f"Fight Started. \n"
            f"Your CS: {self.Sheet.CombatSkill} | Enemy CS: {self.Fight.EnemyCombatSkill} | Combat Ratio: {Ratio}\n"
            f"Enemy EP: {self.Fight.EnemyEndurance.Current}/{self.Fight.EnemyEndurance.Max}\n"
            f"Use your book's Combat Results Table with (Combat Ratio, Random Number).\n"
            f"Then run: apply <YourDamage> <EnemyDamage>"
        )
    
    def ApplyFightRound(self, YourDamage: int, EnemyDamage: int) -> str:
        if self.Fight is None:
            return "No active fight. Start one with: fight <enemyCS> <enemyEP>"
        
        BeforeYou  = self.Sheet.Endurance.Current
        BeforeEnemy = self.Fight.EnemyEndurance.Current

        self.Sheet.TakeDamage(int(YourDamage))
        self.Fight.EnemyEndurance.Current

        OutcomeLines = [
            f"Round applied. You: {BeforeYou} -> {AfterYou} | Enemy: {BeforeEnemy} -> {AfterEnemy}"
        ]

        if AfterEnemy == 0:
            OutcomeLines.append("Enemy Defeated.")
            self.Fight=None
        
        if AfterYou == 0:
            OutcomeLines.append("You are at 0 endurance. Your life and adventure end here!")
        
        self.Save()
        return "\n".join(OutcomeLines)
    
    def StatusText(self) -> str:
        Lines: list[str] = []
        Lines.append(f"Name: {self.Sheet.Name}")
        Lines.append(f"Book: {self.Sheet.CurrentBook}")
        Lines.append(f"CS: {self.Sheet.CombatSkill}")
        Lines.append(f"EP: {self.Sheet.Endurance.Current}/{self.Sheet.Endurance.Max}")
        Lines.append(f"Gold: {self.Sheet.GoldCrowns}")
        Lines.append(f"Disciplines: {', '.join(self.Sheet.KaiDisciplines) if self.Sheet.KaiDisciplines else '(none)'}")
        Lines.append(f"Weapons: {', '.join(self.Sheet.Inventory.Weapons) if self.Sheet.Inventory.Weapons else '(none)'}")
        Lines.append(f"Backpack: {', '.join(self.Sheet.Inventory.BackpackItems) if self.Sheet.Inventory.BackpackItems else '(none)'}")
        Lines.append(f"Special: {', '.join(self.Sheet.Inventory.SpecialItems) if self.Sheet.Inventory.SpecialItems else '(none)'}")

        if self.Fight is not None:
            Ratio = self.Sheet.CombatSkill - self.Fight.EnemyCombatSkill
            Lines.append(f"Active Fight: Enemy CS {self.Fight.EnemyCombatSkill} | Enemy EP {self.Fight.EnemyEndurance.Current}/{self.Fight.EnemyEndurance.Max} | Ratio {Ratio}")
        
        return "\n".join(Lines)