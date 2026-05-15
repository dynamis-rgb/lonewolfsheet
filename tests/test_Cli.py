from pathlib import Path

from modules.Cli import CliApp
from modules.JsonRepository import JsonRepository


def test_cli_create_and_show(tmp_path, capsys):
    repo = JsonRepository()
    app = CliApp(repo)

    file_path = tmp_path / "character.json"

    # create character
    exit_code = app.Run(["create", str(file_path)])
    assert exit_code == 0
    assert file_path.exists()

    # show character
    exit_code = app.Run(["show", str(file_path)])
    assert exit_code == 0

    output = capsys.readouterr().out
    assert "Lone Wolf" in output
    assert "Combat Skill" in output

def test_cli_heal(tmp_path):
    repo = JsonRepository()
    app = CliApp(repo)

    file_path = tmp_path / "character.json"

    app.Run(["create", str(file_path)])

    exit_code = app.Run(["heal", str(file_path), "3"])

    assert exit_code == 0

    sheet = repo.LoadCharacter(file_path)

    assert sheet.Endurance.Current == sheet.Endurance.Max

def test_cli_damage(tmp_path):
    repo = JsonRepository()
    app = CliApp(repo)

    file_path = tmp_path / "character.json"

    app.Run(["create", str(file_path)])

    app.Run(["damage", str(file_path), "5"])

    sheet = repo.LoadCharacter(file_path)

    assert sheet.Endurance.Current == sheet.Endurance.Max - 5

def test_cli_set_book(tmp_path):
    repo = JsonRepository()
    app = CliApp(repo)

    file_path = tmp_path / "character.json"

    app.Run(["create", str(file_path)])

    exit_code = app.Run(["set-book", str(file_path), "2"])

    assert exit_code == 0

    sheet = repo.LoadCharacter(file_path)

    assert sheet.CurrentBook == 2

def test_cli_add_discipline(tmp_path):
    repo = JsonRepository()
    app = CliApp(repo)

    file_path = tmp_path / "character.json"

    app.Run(["create", str(file_path)])

    exit_code = app.Run(["add-discipline", str(file_path), "Mindblast"])

    assert exit_code == 0

    sheet = repo.LoadCharacter(file_path)

    assert "Mindblast" in sheet.KaiDisciplines

def test_cli_play_quits_immediately(tmp_path, monkeypatch):
    import builtins
    from modules.Cli import CliApp
    from modules.JsonRepository import JsonRepository

    Repo = JsonRepository()
    App = CliApp(Repo)

    SavePath = tmp_path / "character.json"

    Inputs = iter(["quit"])

    def FakeInput(Prompt: str = "") -> str:
        return next(Inputs)

    monkeypatch.setattr(builtins, "input", FakeInput)

    ExitCode = App.Run(["play", str(SavePath)])
    assert ExitCode == 0
    assert SavePath.exists()
