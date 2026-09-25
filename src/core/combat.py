"""
Combat resolution. Deterministic HP subtraction, per the locked design rules:

- Kill trigger = Zone of Control: a predator threatens its own tile AND all
  8 adjacent tiles. A prey unit that ends its move on, or passes through,
  any threatened tile can be attacked.
- Wolf cooldown is per-wolf, not pack-wide.
- Giraffe wounds persist across turns (no HP reset between hits).
- Buffalo's 2-tile water move is vulnerable at the mid-tile: check both
  the intermediate and final tile against every predator's zone of control.
"""
from __future__ import annotations

from typing import List, Tuple

from src.core.agent import PredatorAgent, PreyAgent
from src.core.grid import Grid

Coord = Tuple[int, int]


def zone_of_control(grid: Grid, predator: PredatorAgent) -> List[Coord]:
    """Tiles this predator threatens: its own tile + all adjacent tiles."""
    return [predator.pos] + grid.passable_neighbors(predator.pos) + \
        [n for n in grid.neighbors(predator.pos) if not grid.is_passable(n)]
    # NOTE: impassable neighbors (e.g. river) are still "threatened" for
    # attack-trigger purposes even though a unit can't stand there.


def tiles_crossed(path: List[Coord]) -> List[Coord]:
    """All tiles a unit passes through in one move, start exclusive."""
    return path[1:] if len(path) > 1 else path


def check_attack_triggers(
    grid: Grid,
    predators: List[PredatorAgent],
    prey: PreyAgent,
    move_path: List[Coord],
) -> List[PredatorAgent]:
    """Returns every predator whose zone of control this prey's move crosses."""
    crossed = set(tiles_crossed(move_path))
    triggered = []
    for pred in predators:
        if not pred.alive if hasattr(pred, "alive") else False:
            continue
        if crossed & set(zone_of_control(grid, pred)):
            triggered.append(pred)
    return triggered


def resolve_attack(predator: PredatorAgent, prey: PreyAgent, unit_stats: dict) -> int:
    """
    Applies damage from predator -> prey. Returns damage dealt.
    Caller is responsible for checking predator.can_attack() first and for
    setting predator.cooldown_remaining after a Wolf kill (per-wolf only).
    """
    if not predator.can_attack():
        return 0

    stats = unit_stats[predator.species]
    damage = 9999 if stats.one_shot_kill else stats.damage
    killed = prey.take_damage(damage)

    if predator.species == "wolf" and killed:
        predator.cooldown_remaining = stats.cooldown_after_kill

    if killed and predator.species == "tiger":
        predator.is_constant_chase = True  # "when a prey is killed, predator goes into constant chase"

    return damage


def buffalo_water_crossing_path(grid: Grid, start: Coord, end: Coord) -> List[Coord]:
    """
    Builds the 2-tile water-crossing path for Buffalo so the mid-tile is
    explicitly included and therefore checked by check_attack_triggers.
    Straight-line midpoint; callers should validate both tiles are water.
    """
    mid = ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2)
    return [start, mid, end]
