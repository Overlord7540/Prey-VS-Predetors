"""
STUB - deferred past the v1 core loop.

Scent/danger influence maps were in the original tech spec but are likely
redundant with the explicit PANIC/DESPAIR fcost system already in fsm.py
(see the project review notes in docs/GDD.md, Section "Build Phasing").

If revisited: a simple decaying-value grid per side (predator "danger" map,
prey "scent" map), updated each turn and decayed by a fixed factor, read
by fsm.py as an additional fcost term rather than a replacement for it.
"""
from __future__ import annotations

from typing import Tuple

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
