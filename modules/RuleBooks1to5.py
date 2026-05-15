from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CombatOutcome:
    YouDamage: int
    EnemyDamage: int


class CombatResultsTable:

    def __init__(self, MinRatio: int, MaxRatio: int, Rows: dict[int, list[list[int]]]) -> None:
        self.MinRatio = MinRatio
        self.MaxRatio = MaxRatio
        self.Rows = Rows

    @staticmethod
    def LoadFromJson(FilePath: Path) -> "CombatResultsTable":
        Data = json.loads(FilePath.read_text(encoding="utf-8"))

        Rows = {int(Key): list(Value) for Key, Value in Data["Rows"].items()}

        return CombatResultsTable(
            MinRatio=int(Data["MinRatio"]),
            MaxRatio=int(Data["MaxRatio"]),
            Rows=Rows,
        )

    def ResolveRound(self, CombatRatio: int, RandomNumber: int) -> CombatOutcome:

        if RandomNumber < 0 or RandomNumber > 9:
            raise ValueError("RandomNumber must be between 0 and 9")

        Ratio = max(self.MinRatio, min(self.MaxRatio, int(CombatRatio)))

        Row = self.Rows.get(Ratio)

        if Row is None:
            raise ValueError(f"No CRT row found for ratio {Ratio}")

        if len(Row) != 10:
            raise ValueError(f"CRT row for ratio {Ratio} must have 10 entries")

        Cell = Row[RandomNumber]

        if not isinstance(Cell, list) or len(Cell) != 2:
            raise ValueError(f"Invalid CRT cell at ratio {Ratio}, roll {RandomNumber}")

        return CombatOutcome(
            EnemyDamage=int(Cell[0]),
            YouDamage=int(Cell[1]),
        )
