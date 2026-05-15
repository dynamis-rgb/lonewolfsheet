import builtins

from modules.Cli import CliApp
from modules.DomainModels import CharacterSheet, Endurance
from modules.JsonRepository import JsonRepository


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
