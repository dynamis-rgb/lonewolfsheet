from pathlib import Path

import pytest

from modules.RuleBooks1to5 import CombatResultsTable


def test_CombatResultsTable_LoadsConfiguredRows():
    table_path = Path("configs") / "CombatResultsTable_local.json"

    table = CombatResultsTable.LoadFromJson(table_path)

    assert table.MinRatio == -11
    assert table.MaxRatio == 11
    assert table.Rows[-11][0] == [0, 100]
    assert table.Rows[0][4] == [7, 2]
    assert table.Rows[11][9] == [100, 0]


@pytest.mark.parametrize(
    ("combat_ratio", "random_number", "expected_you", "expected_enemy"),
    [
        (-11, 0, 100, 0),
        (0, 4, 2, 7),
        (7, 9, 0, 100),
        (11, 5, 1, 16),
    ],
)
def test_CombatResultsTable_ResolveRound_ReturnsExpectedValues(
    combat_ratio: int,
    random_number: int,
    expected_you: int,
    expected_enemy: int,
):
    table = CombatResultsTable.LoadFromJson(Path("configs") / "CombatResultsTable_local.json")

    outcome = table.ResolveRound(combat_ratio, random_number)

    assert outcome.YouDamage == expected_you
    assert outcome.EnemyDamage == expected_enemy


def test_CombatResultsTable_ResolveRound_ClampsRatioToBounds():
    table = CombatResultsTable.LoadFromJson(Path("configs") / "CombatResultsTable_local.json")

    low_outcome = table.ResolveRound(-99, 0)
    high_outcome = table.ResolveRound(99, 9)

    assert low_outcome.YouDamage == 100
    assert low_outcome.EnemyDamage == 0
    assert high_outcome.YouDamage == 0
    assert high_outcome.EnemyDamage == 100


@pytest.mark.parametrize("random_number", [-1, 10])
def test_CombatResultsTable_ResolveRound_RejectsInvalidRandomNumber(random_number: int):
    table = CombatResultsTable.LoadFromJson(Path("configs") / "CombatResultsTable_local.json")

    with pytest.raises(ValueError, match="RandomNumber must be between 0 and 9"):
        table.ResolveRound(0, random_number)
