"""Controller contract: detached observations in, movement requests out."""
from dataclasses import dataclass, field
from typing import Protocol
from src.core.agent import Agent, Flock
from src.core.grid import Grid


@dataclass(frozen=True)
class Action:
    destination: tuple[int, int]
    reason: str = ""
    kind: str = "auto"  # auto (controller compatibility), attack, feed, wait
    target_id: str | None = None


@dataclass(frozen=True)
class Observation:
    round_number: int
    actor: Agent
    agents: tuple[Agent, ...]
    grid: Grid
    flock: Flock | None
    legal_destinations: tuple[tuple[int, int], ...]
    unit_stats: dict | None = None
    visible: tuple[tuple[int, int], ...] = ()
    remembered: tuple[tuple[int, int], ...] = ()
    influence: dict = field(default_factory=dict)


class Controller(Protocol):
    def choose_action(self, observation: Observation) -> Action:
        """Return a move or the current position to wait. No live state access."""
        ...
