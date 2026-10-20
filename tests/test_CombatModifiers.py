from dataclasses import replace

import pytest

from modules.AppConfig import InventoryRules, LoadItemCatalog
from modules.DomainModels import CharacterSheet, Endurance
from modules.RuleBooks1to5 import CombatModifiers, RuleBooks1to5


SOMMERSWERD = "Sommerswerd, the Sun-sword"


@pytest.fixture
def rules():
    return RuleBooks1to5(InventoryRules(8, 12))


def sheet():
    return CharacterSheet("Test", 17, Endurance(20, 25))


def test_no_items_means_no_modifiers(rules):
    assert rules.ResolveCombatModifiers(sheet()) == CombatModifiers()


def test_equipped_special_weapon_and_passive_items_stack_once(rules):
    character = sheet()
    character.Inventory.SpecialItems = [SOMMERSWERD, "Shield", "Helmet", "Chainmail Waistcoat"]
    character.Inventory.EquippedWeapon = SOMMERSWERD
    before = character.ToDict()
    result = rules.ResolveCombatModifiers(character)
    assert result.CombatSkillBonus == 10
    assert result.EnduranceBonus == 6
    assert [source.Name for source in result.Sources] == [
        SOMMERSWERD, "Shield", "Helmet", "Chainmail Waistcoat"
    ]
    assert rules.ResolveCombatModifiers(character) == result
    assert character.ToDict() == before
    restored = CharacterSheet.FromDict(before)
    assert rules.ResolveCombatModifiers(restored) == result


def test_unequipped_special_weapon_does_not_contribute(rules):
    character = sheet()
    character.Inventory.SpecialItems = [SOMMERSWERD, "Shield"]
    assert rules.ResolveCombatModifiers(character).CombatSkillBonus == 2
    character.Inventory.EquippedWeapon = SOMMERSWERD
    assert rules.ResolveCombatModifiers(character).CombatSkillBonus == 10
    character.Inventory.UnequipWeapon()
    assert rules.ResolveCombatModifiers(character).CombatSkillBonus == 2


@pytest.mark.parametrize("equipped", [SOMMERSWERD, "Unknown", "Helmet"])
def test_invalid_equipment_grants_no_weapon_bonus(rules, equipped):
    character = sheet()
    character.Inventory.EquippedWeapon = equipped
    assert rules.ResolveCombatModifiers(character) == CombatModifiers()


def test_case_insensitive_ownership_and_duplicate_specials(rules):
    character = sheet()
    character.Inventory.SpecialItems = [SOMMERSWERD.lower(), " shield ", "SHIELD", "helmet"]
    character.Inventory.EquippedWeapon = SOMMERSWERD.upper()
    result = rules.ResolveCombatModifiers(character)
    assert result.CombatSkillBonus == 10
    assert result.EnduranceBonus == 2
    assert len(result.Sources) == 3


def test_consumables_backpack_items_and_unknown_items_are_not_passive(rules):
    character = sheet()
    character.Inventory.BackpackItems = ["Potion of Alether", "Laumspur-4", "Shield"]
    character.Inventory.SpecialItems = ["Potion of Alether", "Unknown", "Laumspur-4"]
    assert rules.ResolveCombatModifiers(character) == CombatModifiers()


def test_removing_items_recomputes_modifiers(rules):
    character = sheet()
    character.Inventory.SpecialItems = [SOMMERSWERD, "Shield", "Helmet"]
    character.Inventory.EquippedWeapon = SOMMERSWERD
    character.Inventory.RemoveSpecialItem(SOMMERSWERD)
    character.Inventory.RemoveSpecialItem("Helmet")
    result = rules.ResolveCombatModifiers(character)
    assert result.CombatSkillBonus == 2
    assert result.EnduranceBonus == 0


def test_regular_weapon_bonuses_switch_and_preserve_negative_values():
    catalog = dict(LoadItemCatalog())
    catalog["Sword"] = replace(catalog["Sword"], CombatSkillBonus=3, EnduranceBonus=-2)
    rules = RuleBooks1to5(InventoryRules(8, 12), catalog)
    character = sheet()
    character.Inventory.Weapons = ["sword", "Axe"]
    character.Inventory.EquippedWeapon = "SWORD"
    result = rules.ResolveCombatModifiers(character)
    assert (result.CombatSkillBonus, result.EnduranceBonus) == (3, -2)
    character.Inventory.EquippedWeapon = "Axe"
    assert rules.ResolveCombatModifiers(character) == CombatModifiers()


def test_special_weapon_in_wrong_category_does_not_grant_bonus(rules):
    character = sheet()
    character.Inventory.Weapons = [SOMMERSWERD]
    character.Inventory.EquippedWeapon = SOMMERSWERD
    assert rules.ResolveCombatModifiers(character) == CombatModifiers()
