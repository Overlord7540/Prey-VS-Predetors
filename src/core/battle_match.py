"""Step one skirmish. Wildlife simulation is a different match."""
from __future__ import annotations

import random
from dataclasses import dataclass

from src.ai.fov import can_see, visible_tiles
from src.core.battle import Battle
from src.core.grid import Grid
from src.core.movement import reachable_paths

SIDES = ("hunter", "herd")
COVER = 4


@dataclass
class Combatant:
    name: str
    body: str
    side: str
    pos: tuple[int, int]
    hp: int
    move_range: int
    damage: int
    damage_spread: int
    alive: bool = True

    @property
    def agent_id(self) -> str:
        return self.name


@dataclass(frozen=True)
class UnitView:
    name: str
    side: str
    pos: tuple[int, int]
    hp: int
    move_range: int
    damage: int
    damage_spread: int


@dataclass(frozen=True)
class BattleView:
    round_number: int
    actor: UnitView
    allies: tuple[UnitView, ...]
    enemies: tuple[UnitView, ...]
    legal_destinations: tuple[tuple[int, int], ...]
    attacks: tuple[tuple[tuple[int, int], str], ...]
    bearing: int
    grid: Grid


@dataclass(frozen=True)
class BattleAction:
    destination: tuple[int, int]
    target: str | None = None
    reason: str = ""


def engagement(grid: Grid, actor: Combatant, units: tuple[Combatant, ...] | list[Combatant]):
    """Legal tiles and blows from what this fighter can see. Hidden enemies are omitted."""
    seen = visible_tiles(grid, actor.pos, grid.rules.sight_range)
    legal = tuple(tile for tile in reachable_paths(grid, actor, units, actor) if tile in seen)
    attacks = tuple(
        (tile, enemy.name)
        for enemy in units
        if enemy.alive and enemy.side != actor.side
        for tile in legal
        if _can_strike(grid, tile, enemy.pos)
    )
    return seen, legal, attacks


def _can_strike(grid: Grid, origin: tuple[int, int], target: tuple[int, int]) -> bool:
    return Grid.chebyshev_distance(origin, target) == 1 and can_see(grid, origin, target)


def _view_of(unit: Combatant) -> UnitView:
    return UnitView(unit.name, unit.side, unit.pos, unit.hp, unit.move_range, unit.damage, unit.damage_spread)


class BattleMatch:
    def __init__(self, battle: Battle, controller, seed: int | None = None, max_rounds: int = 30):
        self.grid = battle.grid
        self._controllers = {side: controller for side in SIDES} if not isinstance(controller, dict) else controller
        if set(self._controllers) != set(SIDES):
            raise ValueError("A battle needs a hunter controller and a herd controller")
        self.max_rounds = max_rounds
        self.rng = random.Random(seed)
        self.round = 1
        self.finished = False
        self.winner: str | None = None
        self.events: list[dict] = []
        self.combatants = tuple(
            Combatant(fighter.name, fighter.body, fighter.side, fighter.pos, fighter.hp,
                      fighter.move_range, fighter.damage, fighter.damage_spread)
            for fighter in battle.fighters)
        self._order = {side: tuple(unit for unit in self.combatants if unit.side == side) for side in SIDES}
        self._phase = 0
        self._index = 0

    def fighter(self, name: str) -> Combatant:
        return next(unit for unit in self.combatants if unit.name == name)

    def step(self) -> None:
        if self.finished:
            return
        actor = self._next_actor()
        if actor is None:
            return
        view = self._view(actor)
        self._resolve(actor, view, self._controllers[actor.side].choose_action(view))

    def apply(self, action: BattleAction) -> None:
        """Resolve the fighter who is due, using a person's chosen action."""
        if self.finished:
            return
        actor = self._next_actor()
        if actor is None:
            return
        self._resolve(actor, self._view(actor), action)

    def pending_actor(self) -> Combatant | None:
        phase, index, round_no, finished = self._phase, self._index, self.round, self.finished
        while not finished:
            roster = self._order[SIDES[phase]]
            while index < len(roster):
                unit = roster[index]
                index += 1
                if unit.alive:
                    return unit
            if phase == 0:
                phase, index = 1, 0
                continue
            if round_no >= self.max_rounds:
                return None
            round_no += 1
            phase, index = 0, 0
        return None

    def _resolve(self, actor: Combatant, view: BattleView, action: BattleAction) -> None:
        destination = action.destination if action.destination in view.legal_destinations else actor.pos
        if destination != actor.pos:
            actor.pos = destination
            self.events.append({"kind": "move", "actor": actor.name, "destination": destination})
        else:
            self.events.append({"kind": "wait", "actor": actor.name})
        target_name = action.target if (destination, action.target) in view.attacks else None
        if target_name is not None:
            self._strike(actor, self.fighter(target_name))
        self._check_winner()

    def _next_actor(self) -> Combatant | None:
        while not self.finished:
            roster = self._order[SIDES[self._phase]]
            while self._index < len(roster):
                unit = roster[self._index]
                self._index += 1
                if unit.alive:
                    return unit
            if self._phase == 0:
                self._phase = 1
                self._index = 0
                continue
            if self.round >= self.max_rounds:
                self.finished = True
                return None
            self.round += 1
            self._phase = 0
            self._index = 0
        return None

    def _view(self, actor: Combatant) -> BattleView:
        seen, legal, attacks = engagement(self.grid, actor, self.combatants)
        visible_enemies = []
        for enemy in self.combatants:
            if not enemy.alive or enemy.side == actor.side:
                continue
            if enemy.pos in seen or any(name == enemy.name for _, name in attacks):
                visible_enemies.append(_view_of(enemy))
        allies = tuple(_view_of(unit) for unit in self.combatants if unit.alive and unit.side == actor.side and unit is not actor)
        return BattleView(
            self.round, _view_of(actor), allies, tuple(visible_enemies), legal, attacks,
            1 if actor.side == "hunter" else -1, self.grid,
        )

    def _strike(self, actor: Combatant, target: Combatant) -> None:
        low = max(1, actor.damage - actor.damage_spread)
        high = actor.damage + actor.damage_spread
        damage = self.rng.randint(low, high)
        if self.grid.tiles[target.pos[0]][target.pos[1]] == "chokepoint":
            damage = max(1, damage - COVER)
        damage = min(target.hp, damage)
        target.hp -= damage
        if target.hp == 0:
            target.alive = False
        self.events.append({"kind": "attack", "actor": actor.name, "target": target.name, "damage": damage})

    def _check_winner(self) -> None:
        living = {side: any(unit.alive for unit in roster) for side, roster in self._order.items()}
        if not living["hunter"]:
            self.winner, self.finished = "herd", True
        elif not living["herd"]:
            self.winner, self.finished = "hunter", True
