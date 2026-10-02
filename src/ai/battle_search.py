"""Two-ply skirmish search. One own action, then the best visible reply."""
from __future__ import annotations

import copy

from src.core.battle_match import COVER, BattleAction, BattleView, Combatant, engagement

REASON = "Search"


class SearchBattleController:
    def choose_action(self, view: BattleView) -> BattleAction:
        actor, allies, enemies = _copies(view)
        best_action = None
        best_key = None
        for action in _candidates(view):
            key = _key(view, actor, allies, enemies, action)
            if best_key is None or key > best_key:
                best_key = key
                best_action = action
        return best_action


def _candidates(view: BattleView) -> list[BattleAction]:
    blows = [BattleAction(destination, target, REASON) for destination, target in view.attacks]
    tiles = view.legal_destinations
    if not view.enemies:
        safe = tuple(tile for tile in tiles if view.grid.tiles[tile[0]][tile[1]] != "chokepoint")
        if safe:
            tiles = safe
    quiet = [BattleAction(tile, None, REASON) for tile in tiles]
    return blows + quiet


def _key(view: BattleView, actor: Combatant, allies: list[Combatant], enemies: list[Combatant],
         action: BattleAction) -> tuple:
    actor = copy.copy(actor)
    allies = [copy.copy(unit) for unit in allies]
    enemies = [copy.copy(unit) for unit in enemies]
    actor.pos = action.destination
    dealt = 0.0
    if action.target is not None:
        target = next(unit for unit in enemies if unit.name == action.target)
        dealt = expected_damage(actor, target.hp, _covered(view, target.pos))
        if dealt >= target.hp:
            target.alive = False
    reply = _best_reply(view, [actor, *allies], enemies)
    progress = view.bearing * (action.destination[0] - view.actor.pos[0])
    drift = abs(action.destination[0] - view.actor.pos[0]) + abs(action.destination[1] - view.actor.pos[1])
    return (dealt - reply, progress, -drift, action.destination, action.target or "")


def _best_reply(view: BattleView, friendlies: list[Combatant], enemies: list[Combatant]) -> float:
    worst = 0.0
    for enemy in enemies:
        if not enemy.alive:
            continue
        _, _, attacks = engagement(view.grid, enemy, [*friendlies, *enemies])
        for _tile, target_name in attacks:
            target = next(unit for unit in friendlies if unit.name == target_name)
            if target.alive:
                worst = max(worst, expected_damage(enemy, target.hp, _covered(view, target.pos)))
    return worst


def expected_damage(attacker: Combatant, hp: int, covered: bool) -> float:
    low = max(1, attacker.damage - attacker.damage_spread)
    high = attacker.damage + attacker.damage_spread
    rolls = range(low, high + 1)
    if covered:
        rolls = [max(1, roll - COVER) for roll in rolls]
    return sum(min(hp, roll) for roll in rolls) / (high - low + 1)


def _covered(view: BattleView, pos: tuple[int, int]) -> bool:
    return view.grid.tiles[pos[0]][pos[1]] == "chokepoint"


def _copies(view: BattleView) -> tuple[Combatant, list[Combatant], list[Combatant]]:
    return _unit(view.actor), [_unit(unit) for unit in view.allies], [_unit(unit) for unit in view.enemies]


def _unit(unit) -> Combatant:
    return Combatant(unit.name, "", unit.side, unit.pos, unit.hp, unit.move_range, unit.damage, unit.damage_spread)
