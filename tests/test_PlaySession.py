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


def test_temporary_effects_stack_with_persistent_bonuses_and_expire(session):
    session.Sheet.Inventory.SpecialItems = ["Shield"]
    session.StartFight(20, 100)
    session.AddTemporaryCombatModifier("Potion", 2)
    session.AddTemporaryCombatModifier("Blessing", 3, Rounds=2)
    session.AddTemporaryCombatModifier("Wound", -1, Rounds=1)
    assert session.GetEffectiveCombatSkill() == 23
    assert session.GetCombatRatio() == 3
    session.ApplyFightRound(0, 0)
    assert session.GetEffectiveCombatSkill() == 24
    session.ApplyFightRound(0, 0)
    assert session.GetEffectiveCombatSkill() == 21
    assert session.Sheet.CombatSkill == 17
    session.StartFight(20, 100)
    assert session.TemporaryModifiers == []
    assert session.GetEffectiveCombatSkill() == 19


def test_mindblast_toggle_requires_discipline_and_never_stacks_with_itself(session):
    session.StartFight(20, 100)
    with pytest.raises(ValueError, match="discipline"):
        session.SetMindblast(True)
    session.Sheet.KaiDisciplines = [" mindblast "]
    session.SetMindblast(True)
    session.SetMindblast(True)
    session.AddTemporaryCombatModifier("Potion", 2)
    assert session.GetEffectiveCombatSkill() == 21
    assert "Mindblast: on" in session.StatusText()
    session.SetMindblast(False)
    assert session.GetEffectiveCombatSkill() == 19
    session.SetMindblast(True)
    session.StartFight(20, 100)
    assert not session.MindblastEnabled


@pytest.mark.parametrize("your_damage,enemy_damage", [(0, 100), (30, 0), (30, 100)])
def test_fight_end_clears_effects_and_mindblast(session, your_damage, enemy_damage):
    session.Sheet.KaiDisciplines = ["Mindblast"]
    session.StartFight(20, 100)
    session.SetMindblast(True)
    session.AddTemporaryCombatModifier("Potion", 2)
    session.ApplyFightRound(your_damage, enemy_damage)
    assert session.Fight is None
    assert session.TemporaryModifiers == []
    assert not session.MindblastEnabled
    assert session.GetEffectiveCombatSkill() == 17


def test_combat_potion_consumes_one_and_stacks_without_saving_bonus(session):
    session.Sheet.Inventory.BackpackItems = ["Potion of Alether", "Potion of Alether"]
    session.StartFight(20, 100)
    session.UseCombatPotion("POTION OF ALETHER")
    assert session.GetEffectiveCombatSkill() == 19
    assert session.Sheet.Inventory.BackpackItems == ["Potion of Alether"]
    session.UseCombatPotion("Potion of Alether")
    assert session.GetEffectiveCombatSkill() == 21
    assert session.Sheet.Inventory.BackpackItems == []
    saved = session.Repo.LoadCharacter(session.SavePath)
    assert saved.Inventory.BackpackItems == []
    assert saved.CombatSkill == 17
    reloaded = PlaySession.CreateOrLoad(session.Repo, session.SavePath)
    assert reloaded.TemporaryModifiers == []
    assert reloaded.GetEffectiveCombatSkill() == 17
    with pytest.raises(ValueError, match="not owned"):
        session.UseCombatPotion("Potion of Alether")


@pytest.mark.parametrize("name", ["Meal", "Helmet", "Laumspur-4", "Unknown"])
def test_invalid_potion_does_not_change_inventory_or_effects(session, name):
    session.Sheet.Inventory.BackpackItems = [name]
    session.StartFight(20, 100)
    with pytest.raises(ValueError, match="consumable"):
        session.UseCombatPotion(name)
    assert session.Sheet.Inventory.BackpackItems == [name]
    assert session.TemporaryModifiers == []


def test_effects_require_active_fight(session):
    session.Sheet.KaiDisciplines = ["Mindblast"]
    for action in (
        lambda: session.AddTemporaryCombatModifier("Test", 2),
        lambda: session.SetMindblast(True),
        lambda: session.UseCombatPotion("Potion of Alether"),
    ):
        with pytest.raises(ValueError, match="No active fight"):
            action()


@pytest.mark.parametrize("rounds,error", [(0, ValueError), (-1, ValueError), (True, TypeError), (1.5, TypeError)])
def test_invalid_duration_does_not_add_effect(session, rounds, error):
    session.StartFight(20, 100)
    with pytest.raises(error):
        session.AddTemporaryCombatModifier("Test", 2, Rounds=rounds)
    assert session.TemporaryModifiers == []


def test_remove_effects_by_source_and_clear(session):
    session.StartFight(20, 100)
    session.AddTemporaryCombatModifier("Potion", 2)
    session.AddTemporaryCombatModifier("Potion", 2)
    session.AddTemporaryCombatModifier("Other", -1)
    assert session.RemoveTemporaryCombatModifiers(" POTION ") == 2
    assert session.GetTemporaryCombatSkillBonus() == -1
    session.ClearTemporaryCombatModifiers()
    assert session.GetTemporaryCombatSkillBonus() == 0


def test_automatic_round_uses_bonus_before_expiring_it(session):
    session.StartFight(20, 100)
    session.AddTemporaryCombatModifier("One round", 5, Rounds=1)

    class FixedRng:
        def randint(self, lower, upper):
            return 4

    session.Rng = FixedRng()
    expected = session.CtrTable.ResolveRound(2, 4)
    text = session.ResolveAutomaticRound()
    assert "Combat Ratio: 2" in text
    assert session.Sheet.Endurance.Current == 30 - expected.YouDamage
    assert session.GetTemporaryCombatSkillBonus() == 0


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
