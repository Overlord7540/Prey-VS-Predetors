"""Structured simulation output; no user-interface wording."""
from dataclasses import dataclass
from typing import Dict


@dataclass
class SimulationEvent:
    turn: int
    kind: str  # kill | hit | depleted
    pos: tuple[int, int]
    actor: str
    target: str = ""
    damage: int = 0


@dataclass
class TurnRecord:
    turn: int
    predator_positions: Dict[str, tuple]
    prey_positions: Dict[str, tuple]
    prey_alive_count: int
    resources_remaining: int


@dataclass(frozen=True)
class ActionRecord:
    actor: str
    side: str
    before: tuple[int, int]
    after: tuple[int, int]
    state_before: str | None
    state_after: str | None
    food_consumed: int
    damage: int
    kills: int
    alive: bool
