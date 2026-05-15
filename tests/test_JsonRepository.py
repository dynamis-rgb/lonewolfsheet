import pytest

from modules.DomainModels import CharacterSheet, Endurance
from modules.JsonRepository import JsonLoadError, JsonRepository, JsonSchemaVersionError


def _MakeSheet() -> CharacterSheet:
    return CharacterSheet(
        Name="Lone Wolf",
        CombatSkill=17,
        Endurance=Endurance(Current=22, Max=22),
        KaiDisciplines=["Camouflage", "Hunting", "Tracking", "Sixth Sense", "Healing"],
        GoldCrowns=12,
        CurrentBook=1,
        CurrentSection=42,
    )


def test_JsonRepository_SaveThenLoad_RoundTrips(tmp_path):
    Repo = JsonRepository()
    Sheet = _MakeSheet()

    FilePath = tmp_path / "character.json"
    Repo.SaveCharacter(Sheet, FilePath)

    Loaded = Repo.LoadCharacter(FilePath)

    assert Loaded.Name == Sheet.Name
    assert Loaded.CombatSkill == Sheet.CombatSkill
    assert Loaded.Endurance.Current == Sheet.Endurance.Current
    assert Loaded.Endurance.Max == Sheet.Endurance.Max
    assert Loaded.KaiDisciplines == Sheet.KaiDisciplines
    assert Loaded.GoldCrowns == Sheet.GoldCrowns
    assert Loaded.CurrentBook == Sheet.CurrentBook
    assert Loaded.CurrentSection == Sheet.CurrentSection


def test_JsonRepository_LoadCharacter_RejectsInvalidJson(tmp_path):
    Repo = JsonRepository()
    FilePath = tmp_path / "bad.json"
    FilePath.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(JsonLoadError):
        Repo.LoadCharacter(FilePath)


def test_JsonRepository_LoadCharacter_RejectsUnsupportedSchemaVersion(tmp_path):
    Repo = JsonRepository()
    FilePath = tmp_path / "bad_schema.json"
    FilePath.write_text('{"SchemaVersion": 999, "Character": {}}', encoding="utf-8")

    with pytest.raises(JsonSchemaVersionError):
        Repo.LoadCharacter(FilePath)
