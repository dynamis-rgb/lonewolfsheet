from modules.DomainModels import CharacterSheet, Endurance


def test_Endurance_Heal_DoesNotExceedMax():
    Value = Endurance(Current=20, Max=22)
    Value.Heal(10)
    assert Value.Current == 22


def test_Endurance_TakeDamage_DoesNotGoBelowZero():
    Value = Endurance(Current=5, Max=22)
    Value.TakeDamage(999)
    assert Value.Current == 0


def test_CharacterSheet_SpendGold_FailsWhenInsufficient():
    Sheet = CharacterSheet(Name="Test", CombatSkill=15, Endurance=Endurance(Current=10, Max=10), GoldCrowns=3)
    Ok = Sheet.SpendGold(5)
    assert Ok is False
    assert Sheet.GoldCrowns == 3


def test_CharacterSheet_SpendGold_SucceedsAndDecrements():
    Sheet = CharacterSheet(Name="Test", CombatSkill=15, Endurance=Endurance(Current=10, Max=10), GoldCrowns=10)
    Ok = Sheet.SpendGold(7)
    assert Ok is True
    assert Sheet.GoldCrowns == 3


def test_CharacterSheet_AddDiscipline_DedupesAndIgnoresBlank():
    Sheet = CharacterSheet(Name="Test", CombatSkill=15, Endurance=Endurance(Current=10, Max=10))
    Sheet.AddDiscipline("Healing")
    Sheet.AddDiscipline("Healing")
    Sheet.AddDiscipline("   ")
    assert Sheet.KaiDisciplines == ["Healing"]