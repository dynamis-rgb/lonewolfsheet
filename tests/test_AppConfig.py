import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from modules.AppConfig import (
    DisciplineDefinition, ItemDefinition, LoadDisciplineCatalog, LoadInventoryRules, LoadItemCatalog,
)


def test_LoadDisciplineCatalog_TypedImmutableAndIndependentOfCwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    catalog = LoadDisciplineCatalog()
    assert len(catalog) == 10
    assert all(isinstance(value, DisciplineDefinition) for value in catalog.values())
    assert catalog["Mindblast"].Description == ""
    assert catalog["Mindblast"].AvailableBooks == (1, 2, 3, 4, 5)
    with pytest.raises(TypeError):
        catalog["New"] = catalog["Mindblast"]
    with pytest.raises(FrozenInstanceError):
        catalog["Mindblast"].Description = "Changed"


@pytest.mark.parametrize("field,value,error", [
    ("Description", None, TypeError),
    ("Description", 1, TypeError),
    ("AvailableBooks", "1", TypeError),
    ("AvailableBooks", [True], TypeError),
    ("AvailableBooks", [1.5], TypeError),
    ("AvailableBooks", ["1"], TypeError),
    ("AvailableBooks", [0], ValueError),
    ("AvailableBooks", [-1], ValueError),
    ("AvailableBooks", [1, 1], ValueError),
])
def test_LoadDisciplineCatalog_InvalidFields(monkeypatch, field, value, error):
    raw = {"Description": "", "AvailableBooks": [1]}
    raw[field] = value
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: json.dumps({"Disciplines": {"Test": raw}}))
    with pytest.raises(error, match=field):
        LoadDisciplineCatalog()


@pytest.mark.parametrize("disciplines,error", [
    ([], TypeError),
    ({" ": {}}, ValueError),
    ({"Mindblast": []}, TypeError),
    ({"Mindblast": {}, "MINDBLAST": {}}, KeyError),
    ({"Mindblast": {"Description": "", "AvailableBooks": [1]},
      "MINDBLAST": {"Description": "", "AvailableBooks": [1]}}, ValueError),
])
def test_LoadDisciplineCatalog_InvalidStructure(monkeypatch, disciplines, error):
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: json.dumps({"Disciplines": disciplines}))
    with pytest.raises(error):
        LoadDisciplineCatalog()


def test_LoadDisciplineCatalog_PreservesDescriptionsAndFutureBooks(monkeypatch):
    raw = {"Description": "A discipline description.", "AvailableBooks": [1, 6, 12]}
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: json.dumps({"Disciplines": {"Test": raw}}))
    assert LoadDisciplineCatalog()["Test"] == DisciplineDefinition(
        "A discipline description.", (1, 6, 12)
    )


def test_LoadItemCatalog_LoadsTypedDefinitionsFromAnyDirectory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    catalog = LoadItemCatalog()
    assert all(isinstance(item, ItemDefinition) for item in catalog.values())
    assert catalog["Meal"].IsConsumable is True
    assert catalog["Rope-2"].SlotCost == 2
    assert catalog["Sommerswerd, the Sun-sword"].CombatSkillBonus == 8
    assert catalog["Helmet"].EnduranceBonus == 2
    assert catalog["Sword"].WeaponTypes == ("Sword",)
    assert catalog["Laumspur-4"].RestoresEndurance == 4
    assert LoadInventoryRules().MaxBackpackItems == 8
    with pytest.raises(TypeError):
        catalog["New"] = catalog["Meal"]
    with pytest.raises(FrozenInstanceError):
        catalog["Meal"].SlotCost = 2


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("Category", "unknown", ValueError),
        ("SlotCost", -1, ValueError),
        ("SlotCost", True, TypeError),
        ("IsWeapon", 1, TypeError),
        ("IsConsumable", "false", TypeError),
        ("CombatSkillBonus", True, TypeError),
        ("EnduranceBonus", 2.5, TypeError),
        ("WeaponTypes", "Sword", TypeError),
        ("WeaponTypes", [1], TypeError),
        ("RestoresEndurance", -1, ValueError),
    ],
)
def test_LoadItemCatalog_RejectsInvalidDefinitions(monkeypatch, field, value, error):
    raw = dict(
        Category="backpack", SlotCost=1, IsWeapon=False, IsConsumable=False,
        CombatSkillBonus=0, EnduranceBonus=0,
    )
    raw[field] = value
    monkeypatch.setattr(Path, "read_text", lambda *args, **kwargs: json.dumps({"Items": {"Test": raw}}))
    with pytest.raises(error, match=field):
        LoadItemCatalog()


def test_LoadItemCatalog_DefaultsOptionalFields(monkeypatch):
    raw = dict(
        Category="backpack", SlotCost=1, IsWeapon=False, IsConsumable=False,
        CombatSkillBonus=-1, EnduranceBonus=0,
    )
    monkeypatch.setattr(Path, "read_text", lambda *args, **kwargs: json.dumps({"Items": {"Test": raw}}))
    item = LoadItemCatalog()["Test"]
    assert item.WeaponTypes == ()
    assert item.RestoresEndurance == 0
    assert item.CombatSkillBonus == -1
