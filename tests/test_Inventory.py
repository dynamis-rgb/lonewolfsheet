from modules.DomainModels import Inventory


def test_Inventory_AddWeapon_Dedupes():
    Inv = Inventory()
    assert Inv.AddWeapon("Sword") is True
    assert Inv.AddWeapon("Sword") is False
    assert Inv.Weapons == ["Sword"]


def test_Inventory_AddBackpack_AllowsDuplicates():
    Inv = Inventory()
    assert Inv.AddBackpackItem("Meal") is True
    assert Inv.AddBackpackItem("Meal") is True
    assert Inv.BackpackItems == ["Meal", "Meal"]