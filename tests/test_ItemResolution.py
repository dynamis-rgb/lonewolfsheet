import pytest

from modules.AppConfig import InventoryRules, LoadItemCatalog
from modules.RuleBooks1to5 import RuleBooks1to5


@pytest.fixture
def rules():
    return RuleBooks1to5(InventoryRules(MaxBackpackItems=8, MaxSpecialItems=12))


@pytest.mark.parametrize(
    "query,name",
    [
        ("  mEaL  ", "Meal"),
        ("sword", "Sword"),
        ("SOMM", "Sommerswerd, the Sun-sword"),
        ("perfumed", "Tablet of Perfumed Soap"),
        ("spear", "Spear"),
    ],
)
def test_resolves_canonical_name_and_definition(rules, query, name):
    result = rules.ResolveItem(query)
    assert result.Status == "found"
    assert result.Name == name
    assert result.Definition is rules.GetItemDefinition(name)
    assert result.Candidates == ()


@pytest.mark.parametrize(
    "query,candidates",
    [
        (" ROPE ", ("Rope-1", "Rope-2")),
        ("blanket", ("Blanket",)),
        ("language", ("Message (in Giak language)", "Scroll (in Giak language)")),
    ],
)
def test_matching_candidates(rules, query, candidates):
    result = rules.ResolveItem(query)
    if len(candidates) == 1:
        assert result.Status == "found"
        assert result.Name == candidates[0]
    else:
        assert result.Status == "ambiguous"
        assert result.Name is None
        assert result.Definition is None
        assert result.Candidates == candidates


@pytest.mark.parametrize("query", ["", "   ", "unknown item"])
def test_no_match(rules, query):
    result = rules.ResolveItem(query)
    assert result.Status == "not_found"
    assert result.Name is None
    assert result.Definition is None
    assert result.Candidates == ()


def test_exact_lookup_does_not_accept_partial_names(rules):
    assert rules.GetItemDefinition(" SWORD ") is rules.ItemCatalog["Sword"]
    assert rules.GetItemDefinition("swo") is None
    assert rules.GetItemDefinition("") is None


def test_prefix_matches_take_priority_over_substrings():
    item = LoadItemCatalog()["Sword"]
    catalog = {name: item for name in ("Blue Sword", "Swordfish", "Swordbreaker")}
    rules = RuleBooks1to5(InventoryRules(8, 12), catalog)
    assert rules.ResolveItem("swordf").Name == "Swordfish"
    assert rules.ResolveItem("sword").Candidates == ("Swordbreaker", "Swordfish")
    unique = RuleBooks1to5(InventoryRules(8, 12), {"Blue Sword": item, "Swordfish": item})
    assert unique.ResolveItem("sword").Name == "Swordfish"


def test_explicit_empty_catalog_stays_empty():
    rules = RuleBooks1to5(InventoryRules(8, 12), {})
    assert rules.ResolveItem("Meal").Status == "not_found"


def test_catalog_rejects_normalized_duplicate_names():
    item = LoadItemCatalog()["Sword"]
    with pytest.raises(ValueError, match="duplicate"):
        RuleBooks1to5(InventoryRules(8, 12), {"Sword": item, "SWORD": item})


def test_unicode_casefold_and_stable_candidate_sorting():
    item = LoadItemCatalog()["Sword"]
    rules = RuleBooks1to5(
        InventoryRules(8, 12), {"Straße": item, "zeta Ring": item, "Alpha Ring": item}
    )
    assert rules.ResolveItem("STRASSE").Name == "Straße"
    assert rules.ResolveItem("ring").Candidates == ("Alpha Ring", "zeta Ring")
