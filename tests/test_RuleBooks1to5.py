from modules.AppConfig import InventoryRules
from modules.DomainModels import CharacterSheet, Endurance
from modules.RuleBooks1to5 import RuleBooks1to5


def _build_sheet(
    backpack_items: list[str] | None = None,
    special_items: list[str] | None = None,
) -> CharacterSheet:
    sheet = CharacterSheet(
        Name="Test",
        CombatSkill=15,
        Endurance=Endurance(Current=20, Max=20),
    )
    sheet.Inventory.BackpackItems = list(backpack_items or [])
    sheet.Inventory.SpecialItems = list(special_items or [])
    return sheet


def test_RuleBooks1to5_CanAddBackpackItem_AllowsWhenUnderLimit():
    rules = RuleBooks1to5(InventoryRules(MaxBackpackItems=8, MaxSpecialItems=12))
    sheet = _build_sheet(backpack_items=["Meal"] * 7)

    result = rules.CanAddBackpackItem(sheet)

    assert result.Allowed is True
    assert result.Reason == ""


def test_RuleBooks1to5_CanAddBackpackItem_RejectsWhenAtLimit():
    rules = RuleBooks1to5(InventoryRules(MaxBackpackItems=8, MaxSpecialItems=12))
    sheet = _build_sheet(backpack_items=["Meal"] * 8)

    result = rules.CanAddBackpackItem(sheet)

    assert result.Allowed is False
    assert result.Reason == "Backpack is full (8/8)."


def test_RuleBooks1to5_CanAddSpecialItem_AllowsWhenUnderLimit():
    rules = RuleBooks1to5(InventoryRules(MaxBackpackItems=8, MaxSpecialItems=12))
    sheet = _build_sheet(special_items=[f"Item {index}" for index in range(11)])

    result = rules.CanAddSpecialItem(sheet)

    assert result.Allowed is True
    assert result.Reason == ""


def test_RuleBooks1to5_CanAddSpecialItem_RejectsWhenAtLimit():
    rules = RuleBooks1to5(InventoryRules(MaxBackpackItems=8, MaxSpecialItems=12))
    sheet = _build_sheet(special_items=[f"Item {index}" for index in range(12)])

    result = rules.CanAddSpecialItem(sheet)

    assert result.Allowed is False


def test_RuleBooks1to5_ValidateInventory_ReturnsNoErrorsWhenWithinLimits():
    rules = RuleBooks1to5(InventoryRules(MaxBackpackItems=8, MaxSpecialItems=12))
    sheet = _build_sheet(
        backpack_items=["Meal"] * 8,
        special_items=[f"Item {index}" for index in range(12)],
    )

    errors = rules.ValidateInventory(sheet)

    assert errors == []


def test_RuleBooks1to5_ValidateInventory_ReturnsErrorsForExceededLimits():
    rules = RuleBooks1to5(InventoryRules(MaxBackpackItems=8, MaxSpecialItems=12))
    sheet = _build_sheet(
        backpack_items=["Meal"] * 9,
        special_items=[f"Item {index}" for index in range(13)],
    )

    errors = rules.ValidateInventory(sheet)

    assert errors == [
        "Backpack item limit exceeded (9/8).",
        "Special item limit exceeded (13/12).",
    ]
