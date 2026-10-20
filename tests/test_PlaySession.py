from pathlib import Path

import pytest

from modules.DomainModels import CharacterSheet, Endurance
from modules.JsonRepository import JsonRepository
from modules.PlaySession import PlaySession
from modules.RuleBooks1to5 import CombatResultsTable


@pytest.fixture
def session(tmp_path):
    return PlaySession(
        Repo=JsonRepository(), SavePath=tmp_path / "character.json",
        Sheet=CharacterSheet("Test", 17, Endurance(30, 30)),
        CtrTable=CombatResultsTable.LoadFromJson(Path("configs/CombatResultsTable_local.json")),
    )


def test_ratio_without_bonuses_and_without_active_fight(session):
    with pytest.raises(ValueError, match="No active fight"):
        session.GetCombatRatio()
    assert session.GetEffectiveCombatSkill() == 17
    session.StartFight(20, 100)
    assert session.GetCombatRatio() == -3


def test_effective_cs_and_ratio_update_when_equipment_changes(session):
    name = "Sommerswerd, the Sun-sword"
    inv = session.Sheet.Inventory
    inv.SpecialItems = [name, "Shield", "Helmet"]
    inv.EquippedWeapon = name
    text = session.StartFight(20, 100)
    assert "Your CS: 27" in text
    assert "Combat Ratio: 7" in text
    assert session.GetCombatRatio() == 7
    assert "Ratio 7" in session.StatusText()
    inv.UnequipWeapon()
    assert session.GetCombatRatio() == -1
    inv.RemoveSpecialItem("Shield")
    assert session.GetCombatRatio() == -3
    assert session.Sheet.CombatSkill == 17
    assert session.Sheet.Endurance.ToDict() == {"Current": 30, "Max": 30}


def test_automatic_round_uses_effective_ratio_and_saves_base_stats(session):
    name = "Sommerswerd, the Sun-sword"
    session.Sheet.Inventory.SpecialItems = [name, "Shield"]
    session.Sheet.Inventory.EquippedWeapon = name
    session.StartFight(20, 100)

    class FixedRng:
        def randint(self, lower, upper):
            return 4

    session.Rng = FixedRng()
    expected = session.CtrTable.ResolveRound(7, 4)
    text = session.ResolveAutomaticRound()
    assert "Combat Ratio: 7" in text
    assert session.Sheet.Endurance.Current == 30 - expected.YouDamage
    assert session.Fight.EnemyEndurance.Current == 100 - expected.EnemyDamage
    saved = session.Repo.LoadCharacter(session.SavePath)
    assert saved.CombatSkill == 17
    assert saved.Inventory.EquippedWeapon == name
    reloaded = PlaySession.CreateOrLoad(session.Repo, session.SavePath)
    assert reloaded.GetEffectiveCombatSkill() == 27
