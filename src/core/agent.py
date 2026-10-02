"""
Agent base classes: Predator and Prey. Pure data + state, no rendering.

Prey states (see docs/ALGORITHMS.md for the full fcost spec):
    NORMAL  -> pathing toward the flock's shared resource goal
    PANIC   -> a predator was spotted; fleeing using fcost
    DESPAIR -> a flock-mate was attacked; fleeing + regrouping using fcost

Predator intents (chosen once per match, species-biased):
    CHASE, AMBUSH, CAMP  (Tiger biases CAMP, Wolf biases AMBUSH)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple

Coord = Tuple[int, int]


class PreyState(Enum):
    NORMAL = auto()
    PANIC = auto()
    DESPAIR = auto()


class PredatorIntent(Enum):
    CHASE = auto()
    AMBUSH = auto()
    CAMP = auto()


@dataclass
class Agent:
    agent_id: str
    species: str
    pos: Coord
    side: str  # "predator" | "prey"
    alive: bool = True


@dataclass
class PreyAgent(Agent):
    hp: int = 0
    max_hp: int = 0
    flock_id: str = ""
    state: PreyState = PreyState.NORMAL
    panic_turns_remaining: int = 0  # blocks new panic triggers flock-wide
    goal: Optional[Coord] = None    # shared flock goal (resource tile)
    adrenaline: bool = False
    adrenaline_cooldown: int = 0  # counted in this animal's activations
    escape_guard: bool = False  # expires after the next activation

    def take_damage(self, amount: int) -> bool:
        """Returns True if this kills the prey."""
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.alive = False
        return not self.alive


@dataclass
class PredatorAgent(Agent):
    pack_id: Optional[str] = None  # None for solitary Tiger
    intent: Optional[PredatorIntent] = None  # rolled once at match start
    cooldown_remaining: int = 0
    is_constant_chase: bool = False  # set True permanently after first kill

    attack_used: bool = False
    resting_this_round: bool = False

    def begin_round(self) -> None:
        self.attack_used = False
        self.resting_this_round = self.cooldown_remaining > 0
        if self.resting_this_round:
            self.cooldown_remaining -= 1

    def can_attack(self) -> bool:
        return not self.attack_used and not self.resting_this_round and self.cooldown_remaining == 0


@dataclass
class Flock:
    """Shared state for a group of PreyAgents (per algorithms.md's flock rules)."""
    flock_id: str
    member_ids: list[str] = field(default_factory=list)
    shared_goal: Optional[Coord] = None
    panic_lock_turns: int = 0  # while > 0, no NEW member may enter PANIC


@dataclass
class Pack:
    """Shared state for a group of PredatorAgents (Wolves only)."""
    pack_id: str
    member_ids: list[str] = field(default_factory=list)
    target_agent_id: Optional[str] = None
