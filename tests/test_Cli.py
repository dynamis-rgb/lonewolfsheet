import builtins

import pytest

from modules.Cli import CliApp
from modules.DomainModels import CharacterSheet, Endurance
from modules.JsonRepository import JsonRepository


@pytest.mark.parametrize(
    "command,backpack,special,weapons,field,expected,message",
    [
        ("add-backpack Helmet", [], [], [], "BackpackItems", [], "use add-special"),
        ("add-weapon Magic Spear", [], [], [], "Weapons", [], "use add-special"),
        ("add-special Meal", [], [], [], "SpecialItems", [], "use add-backpack"),
        ("add-weapon mystery", [], [], [], "Weapons", [], "No matching item"),
        ("add-backpack Rope-2", ["Meal"] * 7, [], [], "BackpackItems", ["Meal"] * 7, "needs 2"),
        ("add-backpack Rope-2", ["Meal"] * 6, [], [], "BackpackItems", ["Meal"] * 6 + ["Rope-2"], "Backpack item added"),
        ("add-backpack Meal", ["Rope-2"] * 4, [], [], "BackpackItems", ["Rope-2"] * 4, "Backpack is full"),
        ("add-special Helmet", [], ["Custom"] * 12, [], "SpecialItems", ["Custom"] * 12, "needs 1"),
        ("add-special Map of Sommerlund", [], ["Custom"] * 12, [], "SpecialItems", ["Custom"] * 12 + ["Map of Sommerlund"], "Special Item added"),
        ("add-weapon SWORD", [], [], ["sword"], "Weapons", ["sword"], "already present"),
        ("add-special HELMET", [], ["helmet"], [], "SpecialItems", ["helmet"], "already present"),
    ],
)
def test_cli_catalog_add_rules(
    tmp_path, monkeypatch, capsys, command, backpack, special, weapons, field, expected, message
):
    repo = JsonRepository()
    path = tmp_path / "character.json"
    sheet = CharacterSheet("Lone Wolf", 17, Endurance(22, 22))
    sheet.Inventory.BackpackItems = backpack
    sheet.Inventory.SpecialItems = special
    sheet.Inventory.Weapons = weapons
    repo.SaveCharacter(sheet, path)
    original = path.read_bytes()
    inputs = iter([command, "quit", "no"])
    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(inputs))
    assert CliApp(repo).Run(["play", str(path)]) == 0
    assert message in capsys.readouterr().out
    assert getattr(repo.LoadCharacter(path).Inventory, field) == expected
    if "added" not in message:
        assert path.read_bytes() == original


@pytest.mark.parametrize("initial_count", [0, 8])
def test_cli_play_add_backpack(tmp_path, monkeypatch, capsys, initial_count):
    repo = JsonRepository()
    save_path = tmp_path / "character.json"
    sheet = CharacterSheet(
        Name="Lone Wolf", CombatSkill=17, Endurance=Endurance(Current=22, Max=22)
    )
    sheet.Inventory.BackpackItems = ["meal"] * initial_count
    repo.SaveCharacter(sheet, save_path)
    inputs = iter(["add-backpack meal", "quit", "no"])
    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(inputs))

    assert CliApp(repo).Run(["play", str(save_path)]) == 0

    output = capsys.readouterr().out
    assert "Unknown command" not in output
    loaded = repo.LoadCharacter(save_path)
    assert len(loaded.Inventory.BackpackItems) == min(initial_count + 1, 8)
    assert ("Backpack item added." in output) == (initial_count < 8)


@pytest.mark.parametrize(
    "commands,items,expected,message",
    [
        (["add-backpack rope", "2"], [], ["Rope-2"], "2. Rope-2"),
        (["add-backpack rope", "abc", "-1", "99", "1"], [], ["Rope-1"], "Enter a number"),
        (["add-backpack rope", "0"], [], [], "selection cancelled"),
        (["add-backpack rope", ""], [], [], "selection cancelled"),
        (["add-backpack nonexistent"], [], [], "No matching item"),
        (["add-backpack MEAL"], [], ["Meal"], "Backpack item added"),
        (["add-backpack perfumed"], [], ["Tablet of Perfumed Soap"], "Backpack item added"),
        (["add-backpack sword"], [], [], "use add-weapon"),
        (["remove-backpack rope", "2"], ["Rope-1", "Rope-2"], ["Rope-1"], "2. Rope-2"),
        (["remove-backpack MEAL"], ["meal", "meal"], ["meal"], "Backpack item removed"),
        (["remove-backpack custom"], ["Custom Trinket"], [], "Backpack item removed"),
        (["remove-backpack rope", "0"], ["Rope-1", "Rope-2"], ["Rope-1", "Rope-2"], "selection cancelled"),
    ],
)
def test_cli_item_resolution(tmp_path, monkeypatch, capsys, commands, items, expected, message):
    repo = JsonRepository()
    save_path = tmp_path / "character.json"
    sheet = CharacterSheet(
        Name="Lone Wolf", CombatSkill=17, Endurance=Endurance(Current=22, Max=22)
    )
    sheet.Inventory.BackpackItems = items
    repo.SaveCharacter(sheet, save_path)
    inputs = iter([*commands, "quit", "no"])
    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(inputs))
    assert CliApp(repo).Run(["play", str(save_path)]) == 0
    assert repo.LoadCharacter(save_path).Inventory.BackpackItems == expected
    output = capsys.readouterr().out
    assert message in output
    assert "Unknown command" not in output


@pytest.mark.parametrize("interruption", [EOFError, KeyboardInterrupt])
def test_cli_item_selection_interruption_cancels(monkeypatch, capsys, interruption):
    def interrupt(_prompt):
        raise interruption

    monkeypatch.setattr(builtins, "input", interrupt)
    assert CliApp(JsonRepository())._ChooseItem(("Rope-1", "Rope-2")) is None
    assert "selection cancelled" in capsys.readouterr().out


@pytest.mark.parametrize(
    "command,choice,field,expected",
    [
        ("add-weapon sw", "2", "Weapons", "Sword"),
        ("add-special map", "1", "SpecialItems", "Map of Sommerlund"),
    ],
)
def test_cli_item_resolution_other_categories(tmp_path, monkeypatch, command, choice, field, expected):
    repo = JsonRepository()
    save_path = tmp_path / "character.json"
    sheet = CharacterSheet(
        Name="Lone Wolf", CombatSkill=17, Endurance=Endurance(Current=22, Max=22)
    )
    repo.SaveCharacter(sheet, save_path)
    inputs = iter([command, choice, "quit", "no"])
    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(inputs))
    assert CliApp(repo).Run(["play", str(save_path)]) == 0
    assert getattr(repo.LoadCharacter(save_path).Inventory, field) == [expected]


def _CreateCharacter(app: CliApp, tmp_path, monkeypatch, rolls: list[int], inputs: list[str]):
    file_path = tmp_path / "character.json"
    roll_iter = iter(rolls)
    input_iter = iter([*inputs, "quit", "no"])

    monkeypatch.setattr("modules.Cli.random.randint", lambda _a, _b: next(roll_iter))
    monkeypatch.setattr(CliApp, "_PromptForSavePath", lambda self: file_path)
    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(input_iter))

    exit_code = app.Run(["create"])
    assert exit_code == 0
    assert file_path.exists()
    return file_path


def test_cli_create_and_show(tmp_path, capsys, monkeypatch):
    repo = JsonRepository()
    app = CliApp(repo)

    file_path = _CreateCharacter(app, tmp_path, monkeypatch, rolls=[6, 2, 9], inputs=["1", "3"])

    exit_code = app.Run(["show", str(file_path)])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "Lone Wolf" in output
    assert "Combat Skill: 16" in output
    assert "Endurance: 29/29" in output
    assert "Section: 1" in output


def test_cli_heal(tmp_path, monkeypatch):
    repo = JsonRepository()
    app = CliApp(repo)

    file_path = _CreateCharacter(app, tmp_path, monkeypatch, rolls=[1, 2, 3], inputs=["2", "3"])

    app.Run(["damage", str(file_path), "5"])
    exit_code = app.Run(["heal", str(file_path), "3"])

    assert exit_code == 0

    sheet = repo.LoadCharacter(file_path)

    assert sheet.Endurance.Current == sheet.Endurance.Max - 2


def test_cli_damage(tmp_path, monkeypatch):
    repo = JsonRepository()
    app = CliApp(repo)

    file_path = _CreateCharacter(app, tmp_path, monkeypatch, rolls=[1, 2, 3], inputs=["2", "3"])

    app.Run(["damage", str(file_path), "5"])

    sheet = repo.LoadCharacter(file_path)

    assert sheet.Endurance.Current == sheet.Endurance.Max - 5


def test_cli_set_book(tmp_path, monkeypatch):
    repo = JsonRepository()
    app = CliApp(repo)

    file_path = _CreateCharacter(app, tmp_path, monkeypatch, rolls=[1, 2, 3], inputs=["2", "3"])

    exit_code = app.Run(["set-book", str(file_path), "2"])

    assert exit_code == 0

    sheet = repo.LoadCharacter(file_path)

    assert sheet.CurrentBook == 2


def test_cli_add_discipline(tmp_path, monkeypatch):
    repo = JsonRepository()
    app = CliApp(repo)

    file_path = _CreateCharacter(app, tmp_path, monkeypatch, rolls=[1, 2, 3], inputs=["2", "3"])

    exit_code = app.Run(["add-discipline", str(file_path), "Mindblast"])

    assert exit_code == 0

    sheet = repo.LoadCharacter(file_path)

    assert "Mindblast" in sheet.KaiDisciplines


def test_cli_play_without_path_can_start_new_character(tmp_path, monkeypatch):
    repo = JsonRepository()
    app = CliApp(repo)
    file_path = tmp_path / "character.json"

    roll_iter = iter([6, 2, 9])
    input_iter = iter(["yes", "1", "3", "quit", "no"])

    monkeypatch.setattr("modules.Cli.random.randint", lambda _a, _b: next(roll_iter))
    monkeypatch.setattr(CliApp, "_PromptForSavePath", lambda self: file_path)
    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(input_iter))

    exit_code = app.Run(["play"])

    assert exit_code == 0
    assert file_path.exists()


def test_cli_create_enters_play_mode_and_can_quit(tmp_path, monkeypatch):
    repo = JsonRepository()
    app = CliApp(repo)
    file_path = tmp_path / "character.json"

    roll_iter = iter([6, 2, 9])
    input_iter = iter(["1", "3", "quit", "no"])

    monkeypatch.setattr("modules.Cli.random.randint", lambda _a, _b: next(roll_iter))
    monkeypatch.setattr(CliApp, "_PromptForSavePath", lambda self: file_path)
    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(input_iter))

    exit_code = app.Run(["create"])

    assert exit_code == 0
    assert file_path.exists()


def test_cli_play_quit_can_save_current_section(tmp_path, monkeypatch):
    repo = JsonRepository()
    app = CliApp(repo)
    save_path = tmp_path / "character.json"

    sheet = CharacterSheet(
        Name="Lone Wolf",
        CombatSkill=17,
        Endurance=Endurance(Current=22, Max=22),
        CurrentBook=1,
        CurrentSection=1,
    )
    repo.SaveCharacter(sheet, save_path)

    inputs = iter(["quit", "yes", "42"])

    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(inputs))

    exit_code = app.Run(["play", str(save_path)])

    assert exit_code == 0
    loaded = repo.LoadCharacter(save_path)
    assert loaded.CurrentSection == 42
