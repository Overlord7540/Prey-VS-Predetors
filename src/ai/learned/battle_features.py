"""Features for one skirmish action. These are not the wildlife tile features."""
from __future__ import annotations

from src.core.battle_match import BattleView
from src.core.grid import Grid

FEATURE_COUNT = 9


def battle_candidates(view: BattleView) -> list[tuple[tuple[int, int], str | None]]:
    actions = [(destination, target) for destination, target in view.attacks]
    actions.extend((tile, None) for tile in view.legal_destinations)
    return actions or [(view.actor.pos, None)]


def action_features(view: BattleView, destination: tuple[int, int], target: str | None) -> list[float]:
    actor = view.actor
    sight = max(1, view.grid.rules.sight_range)
    nearest = min((Grid.chebyshev_distance(destination, enemy.pos) for enemy in view.enemies), default=sight)
    target_hp = 0.0
    if target is not None:
        enemy = next(unit for unit in view.enemies if unit.name == target)
        target_hp = enemy.hp / 60
    covered = view.grid.tiles[destination[0]][destination[1]] == "chokepoint"
    return [
        1.0,
        view.bearing * (destination[0] - actor.pos[0]) / view.grid.height,
        (destination[1] - actor.pos[1]) / view.grid.width,
        Grid.chebyshev_distance(destination, actor.pos) / sight,
        1.0 if target else 0.0,
        target_hp,
        1.0 if covered else 0.0,
        min(nearest, sight) / sight,
        1.0 if actor.side == "hunter" else 0.0,
    ]
