"""Hand-written skirmish policy: strike if a blow is legal, otherwise advance."""
from __future__ import annotations

from src.core.battle_match import BattleAction, BattleView
from src.core.grid import Grid


class RuleBattleController:
    def choose_action(self, view: BattleView) -> BattleAction:
        if view.attacks:
            destination, target = min(view.attacks, key=lambda blow: self._attack_key(view, blow))
            return BattleAction(destination, target, "Strike the weakest enemy in reach")
        destination = min(view.legal_destinations, key=lambda tile: self._advance_key(view, tile))
        reason = "Advance" if destination != view.actor.pos else "Hold"
        return BattleAction(destination, None, reason)

    def _attack_key(self, view: BattleView, blow: tuple[tuple[int, int], str]) -> tuple:
        destination, name = blow
        enemy = next(unit for unit in view.enemies if unit.name == name)
        steps = Grid.chebyshev_distance(view.actor.pos, destination)
        return (enemy.hp, steps, name)

    def _advance_key(self, view: BattleView, tile: tuple[int, int]) -> tuple:
        actor = view.actor.pos
        progress = view.bearing * (tile[0] - actor[0])
        drift = abs(tile[1] - actor[1]) + abs(tile[0] - actor[0])
        return (-progress, drift, tile)
