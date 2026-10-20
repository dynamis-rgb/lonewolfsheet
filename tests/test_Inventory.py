from modules.DomainModels import Inventory

from modules.AppConfig import LoadItemCatalog


def test_Inventory_EquipSpecialWeapon_RequiresWeaponDefinitionAndOwnership():
    catalog = LoadItemCatalog()
    name = "Sommerswerd, the Sun-sword"
    inv = Inventory(SpecialItems=[name, "Helmet"])
    assert inv.EquipWeapon(name) is False
    assert inv.EquipWeapon(name, catalog[name]) is True
    assert inv.EquippedWeapon == name
    assert inv.EquipWeapon("Helmet", catalog["Helmet"]) is False
    assert inv.EquipWeapon("Sword", catalog["Sword"]) is False
    assert inv.EquippedWeapon == name
    assert Inventory.FromDict(inv.ToDict()).EquippedWeapon == name


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


def test_Inventory_EquippedWeapon_RoundTrip():
    Inv = Inventory(Weapons=["Sword", "Axe"])
    assert Inv.EquipWeapon("Sword") is True
    Saved = Inv.ToDict()
    assert Saved["EquippedWeapon"] == "Sword"
    Restored = Inventory.FromDict(Saved)
    assert Restored.EquippedWeapon == "Sword"
    assert Restored.Weapons == ["Sword", "Axe"]


def test_Inventory_FromDict_OldSaveDefaultsToUnequipped():
    Inv = Inventory.FromDict({"Weapons": ["Sword"]})
    assert Inv.EquippedWeapon is None
    assert Inv.ToDict()["EquippedWeapon"] is None


def test_Inventory_RemoveEquippedWeapon_ClearsState():
    Inv = Inventory(Weapons=["Sword"], EquippedWeapon="Sword")
    assert Inv.RemoveWeapon(" Sword ") is True
    assert Inv.EquippedWeapon is None
    assert Inv.Weapons == []
    assert Inventory.FromDict(Inv.ToDict()).EquippedWeapon is None


def test_Inventory_RemoveOtherOrMissingWeapon_PreservesEquipment():
    Inv = Inventory(Weapons=["Sword", "Axe"], EquippedWeapon="Sword")
    assert Inv.RemoveWeapon("Bow") is False
    assert Inv.EquippedWeapon == "Sword"
    assert Inv.RemoveWeapon("Axe") is True
    assert Inv.EquippedWeapon == "Sword"


def test_Inventory_RemoveEquippedSpecialWeapon_ClearsState():
    Name = "Sommerswerd, the Sun-sword"
    Inv = Inventory(SpecialItems=[Name], EquippedWeapon=Name)
    assert Inv.RemoveSpecialItem(Name) is True
    assert Inv.EquippedWeapon is None


def test_Inventory_UnequippedWeapon_RoundTrip():
    Inv = Inventory(Weapons=["Sword"], EquippedWeapon="Sword")
    assert Inv.UnequipWeapon() is True
    assert Inventory.FromDict(Inv.ToDict()).EquippedWeapon is None
