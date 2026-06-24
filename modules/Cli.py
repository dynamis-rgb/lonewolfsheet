from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from modules.AppConfig import LoadAppConfig
from modules.DomainModels import CharacterSheet, Endurance
from modules.JsonRepository import JsonRepository, JsonRepositoryError
from modules.AppConfig import AppConfig



@dataclass(frozen=True)
class CliApp:
    Repo: JsonRepository

    def Run(self, Argv: Sequence[str]) -> int:
        Parser = self._BuildParser()
        Args = Parser.parse_args(list(Argv))

        try:
            if Args.Command == "create":
                return self._HandleCreate()
            if Args.Command == "show":
                return self._HandleShow(Path(Args.Path))
            if Args.Command == "set-book":
                return self._HandleSetBook(Path(Args.Path), int(Args.Book))
            if Args.Command == "add-discipline":
                return self._HandleAddDiscipline(Path(Args.Path), " ".join(Args.Name))
            if Args.Command == "heal":
                return self._HandleHeal(Path(Args.Path), int(Args.Amount))
            if Args.Command == "damage":
                return self._HandleDamage(Path(Args.Path), int(Args.Amount))
            if Args.Command == "play":
                return self._HandlePlay(Path(Args.Path) if Args.Path else None)

            Parser.print_help()
            return 2
        except JsonRepositoryError as Ex:
            print(f"Repository Error: {Ex}")
            return 2
        except ValueError as Ex:
            print(f"Invalid Value: {Ex}")
            return 2

    def _BuildParser(self) -> argparse.ArgumentParser:
        Parser = argparse.ArgumentParser(prog="LoneWolfSheet")

        Subparsers = Parser.add_subparsers(dest="Command", required=True)

        Subparsers.add_parser("create", help="Create a new character JSON file.")

        Show = Subparsers.add_parser("show", help="Show character summary from JSON file.")
        Show.add_argument("Path", help="Path to JSON file to load.")

        SetBook = Subparsers.add_parser("set-book", help="Set current book and save.")
        SetBook.add_argument("Path", help="Path to JSON file to load/save.")
        SetBook.add_argument("Book", help="Current book number.")

        AddDiscipline = Subparsers.add_parser("add-discipline", help="Add a Kai discipline and save.")
        AddDiscipline.add_argument("Path", help="Path to JSON file to load/save.")
        AddDiscipline.add_argument("Name", nargs="+", help="Name of the discipline to add.")

        Heal = Subparsers.add_parser("heal", help="Heal Endurance and save.")
        Heal.add_argument("Path", help="Path to JSON file to load/save.")
        Heal.add_argument("Amount", help="Amount to heal (integer).")

        Damage = Subparsers.add_parser("damage", help="Apply damage to Endurance and save.")
        Damage.add_argument("Path", help="Path to JSON file to load/save.")
        Damage.add_argument("Amount", help="Amount of damage (integer).")

        Play = Subparsers.add_parser(
            "play", 
            help="Interactive play session."
            )
        Play.add_argument(
            "Path",
            nargs="?",
            help="Path to JSON save file"
            )

        return Parser

    def _HandleCreate(self) -> int:
        FilePath = self._RunCharacterCreationFlow()
        return self._HandlePlay(FilePath)

    def _RunCharacterCreationFlow(self) -> Path:
        print("First-Time Character Creation")
        Rolls = []
        for Index in range(3):
            Roll = random.randint(0, 9)
            Rolls.append(Roll)
            print(f"Roll {Index + 1}: {Roll}")

        CsIndex = self._PromptForRollChoice(
            Prompt="Choose roll for Combat Skill [1-3]: ",
            AllowedIndexes={0, 1, 2},
        )
        EpIndex = self._PromptForRollChoice(
            Prompt="Choose roll for Endurance [1-3]: ",
            AllowedIndexes={0, 1, 2} - {CsIndex},
        )

        CombatSkill = 10 + Rolls[CsIndex]
        EndurancePoints = 20 + Rolls[EpIndex]
        FilePath = self._PromptForSavePath()

        Sheet = CharacterSheet(
            Name="Lone Wolf",
            CombatSkill=CombatSkill,
            Endurance=Endurance(Current=EndurancePoints, Max=EndurancePoints),
            CurrentBook=1,
            CurrentSection=1,
        )

        self.Repo.SaveCharacter(Sheet, FilePath)
        print(f"Created character file: {FilePath}")
        print(self._FormatSummary(Sheet))
        return FilePath

    def _HandleShow(self, FilePath: Path) -> int:
        Sheet = self.Repo.LoadCharacter(FilePath)
        print(self._FormatSummary(Sheet))
        return 0

    def _HandleSetBook(self, FilePath: Path, Book: int) -> int:
        Sheet = self.Repo.LoadCharacter(FilePath)
        Before = Sheet.CurrentBook
        Sheet.SetCurrentBook(Book)
        After = Sheet.CurrentBook

        self.Repo.SaveCharacter(Sheet, FilePath)
        print(f"Set current book: {Before} -> {After}")
        return 0

    def _HandleAddDiscipline(self, FilePath: Path, Name: str) -> int:
        Sheet = self.Repo.LoadCharacter(FilePath)
        Before = len(Sheet.KaiDisciplines)
        CleanName = Name.strip()
        Sheet.AddDiscipline(CleanName)
        After = len(Sheet.KaiDisciplines)

        self.Repo.SaveCharacter(Sheet, FilePath)
        if After > Before:
            print(f"Added discipline: {CleanName}")
        else:
            print("Discipline already present or invalid.")
        return 0

    def _HandleHeal(self, FilePath: Path, Amount: int) -> int:
        Sheet = self.Repo.LoadCharacter(FilePath)
        Before = Sheet.Endurance.Current
        Sheet.Heal(Amount)
        After = Sheet.Endurance.Current

        self.Repo.SaveCharacter(Sheet, FilePath)
        print(f"Healed {Amount}. Endurance: {Before} -> {After}")
        return 0

    def _HandleDamage(self, FilePath: Path, Amount: int) -> int:
        Sheet = self.Repo.LoadCharacter(FilePath)
        Before = Sheet.Endurance.Current
        Sheet.TakeDamage(Amount)
        After = Sheet.Endurance.Current

        self.Repo.SaveCharacter(Sheet, FilePath)
        print(f"Damaged {Amount}. Endurance: {Before} -> {After}")
        return 0

    def _FormatSummary(self, Sheet: CharacterSheet) -> str:
        Lines: list[str] = []
        Lines.append(f"Name: {Sheet.Name}")
        Lines.append(f"Book: {Sheet.CurrentBook}")
        Lines.append(f"Section: {Sheet.CurrentSection}")
        Lines.append(f"Kai Rank: {Sheet.KaiRank}")
        Lines.append(f"Combat Skill: {Sheet.CombatSkill}")
        Lines.append(f"Endurance: {Sheet.Endurance.Current}/{Sheet.Endurance.Max}")
        Lines.append(f"Gold Crowns: {Sheet.GoldCrowns}")
        Lines.append(f"Kai Disciplines: {', '.join(Sheet.KaiDisciplines) if Sheet.KaiDisciplines else '(none)'}")

        if Sheet.Inventory.Weapons:
            Lines.append(f"Weapons: {', '.join(Sheet.Inventory.Weapons)}")
        if Sheet.Inventory.BackpackItems:
            Lines.append(f"Backpack: {', '.join(Sheet.Inventory.BackpackItems)}")
        if Sheet.Inventory.SpecialItems:
            Lines.append(f"Special Items: {', '.join(Sheet.Inventory.SpecialItems)}")

        return "\n".join(Lines)
    
    def _HandlePlay(self, FilePath: Path | None) -> int:
        if FilePath is None:
            if self._PromptYesNo("No save file specified. Start a new character? [y/n]: "):
                FilePath = self._RunCharacterCreationFlow()
                return self._HandlePlay(FilePath)
            return 0

        if not FilePath.exists():
            print(f"Save file not found: {FilePath}")
            return 2

        from modules.PlaySession import PlaySession  # local import to keep dependencies simple

        Session = PlaySession.CreateOrLoad(self.Repo, FilePath)

        print("LoneWolfSheet v1 (type 'help' for commands)")
        print(Session.StatusText())

        while True:
            try:
                Raw = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not Raw:
                continue

            Parts = Raw.split()
            Command = Parts[0].lower()
            Args = Parts[1:]

            if Command in ("quit", "exit"):
                self._PromptForSectionOnQuit(Session)
                break

            if Command == "help":
                print(
                    "Commands:\n"
                    "  status\n"
                    "  save\n"
                    "  book <n>\n"
                    "  add-discipline <name>\n"
                    "  heal <n> | damage <n>\n"
                    "  gold +<n> | gold -<n>\n"
                    "  inv\n"
                    "  add-weapon <name> | remove-weapon <name>\n"
                    "  add-backpack <name> | remove-backpack <name>\n"
                    "  add-special <name> | remove-special <name>\n"
                    "  fight <enemyCS> <enemyEP>\n"
                    "  roll\n"
                    "  round\n"
                    "  apply <yourDamage> <enemyDamage>\n"
                    "  quit\n"
                )
                continue

            if Command == "status":
                print(Session.StatusText())
                continue

            if Command == "save":
                Session.Save()
                print(f"Saved: {Session.SavePath}")
                continue

            if Command == "roll":
                Roll = Session.RollRandomNumber()
                print(f"Random Number: {Roll}")
                continue

            if Command == "fight" and len(Args) == 2:
                print(Session.StartFight(int(Args[0]), int(Args[1])))
                continue

            if Command == "round":
                print(Session.ResolveAutomaticRound())
                continue

            if Command == "apply" and len(Args) == 2:
                print(Session.ApplyFightRound(int(Args[0]), int(Args[1])))
                continue

            if Command == "heal" and len(Args) == 1:
                Session.Sheet.Heal(int(Args[0]))
                Session.Save()
                print(Session.StatusText())
                continue

            if Command == "book" and len(Args) == 1:
                Session.Sheet.SetCurrentBook(int(Args[0]))
                Session.Save()
                print(Session.StatusText())
                continue

            if Command == "add-discipline" and Args:
                Session.Sheet.AddDiscipline(" ".join(Args))
                Session.Save()
                print(Session.StatusText())
                continue

            if Command == "damage" and len(Args) == 1:
                Session.Sheet.TakeDamage(int(Args[0]))
                Session.Save()
                print(Session.StatusText())
                continue

            if Command == "gold" and len(Args) == 1:
                Token = Args[0].strip()
                Sign = Token[0]
                Amount = int(Token[1:]) if len(Token) > 1 else 0
                if Sign == "+":
                    Session.Sheet.AddGold(Amount)
                elif Sign == "-":
                    Session.Sheet.SpendGold(Amount)
                Session.Save()
                print(Session.StatusText())
                continue

            if Command == "inv":
                print(
                    f"Weapons: {Session.Sheet.Inventory.Weapons}\n"
                    f"Backpack: {Session.Sheet.Inventory.BackpackItems}\n"
                    f"Special: {Session.Sheet.Inventory.SpecialItems}"
                )
                continue

            # Inventory management (simple; no quoting support yet)
            if Command == "add-weapon" and Args:
                Name = " ".join(Args)
                Added = Session.Sheet.Inventory.AddWeapon(Name)
                Session.Save()
                print("Weapon added." if Added else "Weapon already present or invalid.")
                continue

            if Command == "remove-weapon" and Args:
                Name = " ".join(Args)
                Removed = Session.Sheet.Inventory.RemoveWeapon(Name)
                Session.Save()
                print("Weapon removed." if Removed else "Weapon not found.")
                continue

            if Command == "add-backpack" and Args:
                Name = " ".join(Args)
                Added = Session.Sheet.Inventory.AddBackpackItem(Name)
                Session.Save()
                print("Backpack item added." if Added else "Invalid item name.")
                continue

            if Command == "remove-backpack" and Args:
                Name = " ".join(Args)
                Removed = Session.Sheet.Inventory.RemoveBackpackItem(Name)
                Session.Save()
                print("Backpack item removed." if Removed else "Backpack item not found.")
                continue

            if Command == "add-special" and Args:
                Name = " ".join(Args)
                Added = Session.Sheet.Inventory.AddSpecialItem(Name)
                Session.Save()
                print("Special item added." if Added else "Special item already present or invalid.")
                continue

            if Command == "remove-special" and Args:
                Name = " ".join(Args)
                Removed = Session.Sheet.Inventory.RemoveSpecialItem(Name)
                Session.Save()
                print("Special item removed." if Removed else "Special item not found.")
                continue

            print("Unknown command. Type 'help'.")
        return 0

    def _PromptForRollChoice(self, Prompt: str, AllowedIndexes: set[int]) -> int:
        while True:
            Raw = input(Prompt).strip()
            try:
                Choice = int(Raw)
            except ValueError:
                print("Enter a number from the available choices.")
                continue

            Index = Choice - 1
            if Index in AllowedIndexes:
                return Index

            AllowedText = ", ".join(str(Value + 1) for Value in sorted(AllowedIndexes))
            print(f"Choose one of: {AllowedText}")

    def _PromptForSavePath(self) -> Path:
        while True:
            Raw = input("Enter a save file name: ").strip()
            if not Raw:
                print("Save file name cannot be blank.")
                continue
            if Raw != Path(Raw).name:
                print("Enter a simple file name without folders.")
                continue
            if any(Char in Raw for Char in '<>:"/\\|?*'):
                print("Save file name contains invalid characters.")
                continue
            Config=LoadAppConfig()
            FileName = Raw if Raw.lower().endswith(".json") else f"{Raw}.json"
            FilePath = Config.SaveDirectory / FileName
            if FilePath.exists():
                print(f"Save file already exists: {FilePath}")
                continue
            return FilePath

    def _PromptYesNo(self, Prompt: str) -> bool:
        while True:
            Raw = input(Prompt).strip().lower()
            if Raw in ("y", "yes"):
                return True
            if Raw in ("n", "no"):
                return False
            print("Enter yes or no.")

    def _PromptForSectionOnQuit(self, Session) -> None:
        if not self._PromptYesNo("Do you want to enter your current section before you quit? [y/n]: "):
            return

        while True:
            Raw = input("Enter current section: ").strip()
            try:
                Session.Sheet.SetCurrentSection(int(Raw))
            except ValueError:
                print("Section must be a number 1 or greater.")
                continue

            Session.Save()
            print(f"Saved current section: {Session.Sheet.CurrentSection}")
            return
