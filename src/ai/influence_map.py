"""Enemy falloff used by tactical scores. Built from one observation, not stored on the match."""
from __future__ import annotations

from typing import Iterable, Tuple

Coord = Tuple[int, int]


class InfluenceMap:
    def __init__(self, width: int, height: int, decay: float = 0.9):
        self.width = width
        self.height = height
        self.decay = decay
        self.values: dict[Coord, float] = {}

    def deposit(self, pos: Coord, amount: float) -> None:
        self.values[pos] = self.values.get(pos, 0.0) + amount

    def decay_step(self) -> None:
        for pos in list(self.values):
            self.values[pos] *= self.decay
            if self.values[pos] < 0.01:
                del self.values[pos]

    def value_at(self, pos: Coord) -> float:
        return self.values.get(pos, 0.0)

    def radiate(self, sources: Iterable[Coord], radius: int, visible: set[Coord]) -> dict[Coord, float]:
        """Chebyshev falloff from each source, kept inside the visible set."""
        field: dict[Coord, float] = {}
        for source in sources:
            row, col = source
            for r in range(row - radius, row + radius + 1):
                for c in range(col - radius, col + radius + 1):
                    tile = (r, c)
                    if tile not in visible:
                        continue
                    distance = max(abs(r - row), abs(c - col))
                    if distance > radius:
                        continue
                    field[tile] = field.get(tile, 0.0) + (radius - distance)
        self.values = field
        return field
