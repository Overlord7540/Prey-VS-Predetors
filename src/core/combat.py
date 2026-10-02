"""Seeded bounded damage, per-predator attack limits, and survivor escape effects.

Zone/path helpers are retained for analysis; movement no longer triggers attacks.
"""
from __future__ import annotations

from typing import List, Tuple

from src.core.agent import PredatorAgent, PreyAgent
from src.core.grid import Grid

Coord = Tuple[int, int]
WATER_EXPOSURE = 8


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


def damage_range(predator, unit_stats):
    stats = unit_stats[predator.species]
    return max(1, stats.damage - stats.damage_spread), stats.damage + stats.damage_spread


def resolve_attack(predator: PredatorAgent, prey: PreyAgent, unit_stats: dict, rng=None,
                    exposure: int = 0) -> int:
    """
    Applies damage from predator -> prey. Returns damage dealt.
    Consumes the predator's single attack allowance.
    Cooldown begins after a Wolf kill; begin_round advances it.
    """
    if not predator.alive or not prey.alive or not predator.can_attack() or prey.escape_guard:
        return 0

    stats = unit_stats[predator.species]
    low, high = damage_range(predator, unit_stats)
    damage = rng.randint(low, high) if rng is not None else stats.damage
    damage = min(prey.hp, damage + exposure)
    # The first hit on an unwounded animal leaves them standing so they can bolt.
    if not stats.one_shot_kill and prey.hp == prey.max_hp and prey.hp > 1:
        damage = min(damage, prey.hp - 1)
    predator.attack_used = True
    killed = prey.take_damage(damage)
    if not killed and prey.adrenaline_cooldown == 0:
        prey.adrenaline = True
        prey.escape_guard = True
        prey.adrenaline_cooldown = 3

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
