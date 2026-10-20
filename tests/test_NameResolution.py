import pytest

from modules.AppConfig import DisciplineDefinition, InventoryRules, ItemDefinition
from modules.NameResolution import BuildNameIndex, ResolveName
from modules.RuleBooks1to5 import DisciplineResolutionResult, ItemResolutionResult, RuleBooks1to5


@pytest.mark.parametrize("query,names,status,name,candidates", [
    (" SWORD ", ["Sword", "Swordfish"], "found", "Sword", ()),
    ("swo", ["Sword", "Blue Sword"], "found", "Sword", ()),
    ("blue", ["A Blue Sword"], "found", "A Blue Sword", ()),
    ("swo", ["Swordfish", "Sword", "Blue Sword"], "ambiguous", None, ("Sword", "Swordfish")),
    ("ring", ["Zeta Ring", "Alpha Ring"], "ambiguous", None, ("Alpha Ring", "Zeta Ring")),
    ("STRASSE", ["Straße"], "found", "Straße", ()),
    ("meal", ["meal", "meal"], "found", "meal", ()),
    ("meal", ["meal", "Meal"], "ambiguous", None, ("Meal", "meal")),
    (" ", ["Meal"], "not_found", None, ()),
    ("unknown", ["Meal"], "not_found", None, ()),
    ("Meal", [], "not_found", None, ()),
])
def test_shared_matching(query, names, status, name, candidates):
    result = ResolveName(query, iter(names))
    assert (result.Status, result.Name, result.Candidates) == (status, name, candidates)


@pytest.mark.parametrize("names", [["Sword", " SWORD "], [" "]])
def test_catalog_index_rejects_invalid_names(names):
    with pytest.raises(ValueError):
        BuildNameIndex(names)


@pytest.mark.parametrize("query,name", [
    (" mindBLAST ", "Mindblast"), ("Mindblas", "Mindblast"),
    ("kinship", "Animal Kinship"),
])
def test_typed_discipline_resolution(query, name):
    rules = RuleBooks1to5(InventoryRules(8, 12))
    result = rules.ResolveDiscipline(query)
    assert isinstance(result, DisciplineResolutionResult)
    assert result.Status == "found"
    assert result.Name == name
    assert isinstance(result.Definition, DisciplineDefinition)
    assert result.Definition is rules.GetDisciplineDefinition(name)
    assert result.Candidates == ()
    assert rules.GetDisciplineDefinition("mindblas") is None


def test_typed_results_preserve_unknown_and_ambiguous_states():
    rules = RuleBooks1to5(InventoryRules(8, 12))
    result = rules.ResolveDiscipline("mind")
    assert result.Status == "ambiguous"
    assert result.Candidates == ("Mind Over Matter", "Mindblast", "Mindshield")
    assert result.Name is None and result.Definition is None
    for query in ("", "   ", "unknown"):
        assert rules.ResolveDiscipline(query) == DisciplineResolutionResult("not_found")
    item = rules.ResolveItem("Meal")
    assert isinstance(item, ItemResolutionResult)
    assert isinstance(item.Definition, ItemDefinition)


def test_injected_discipline_catalog_is_independent_and_can_be_empty():
    definition = DisciplineDefinition("Test", (1,))
    rules = RuleBooks1to5(InventoryRules(8, 12), DisciplineCatalog={"Test": definition})
    assert rules.ResolveDiscipline("te").Definition is definition
    assert rules.ResolveDiscipline("Mindblast").Status == "not_found"
    empty = RuleBooks1to5(InventoryRules(8, 12), DisciplineCatalog={})
    assert empty.ResolveDiscipline("Mindblast").Status == "not_found"
    with pytest.raises(ValueError, match="duplicate"):
        RuleBooks1to5(InventoryRules(8, 12), DisciplineCatalog={"Test": definition, "TEST": definition})
