"""
Master turn loop. Zero Pygame imports - fully headless and pytest-able.

Turn structure (locked, GDD Sec. 3):
    1. Predator side acts in full (move + attack for every predator unit)
    2. Prey side acts in full (move + feed for every prey unit)
    3. Check win conditions
    4. Log turn to history

Win conditions (locked):
    - Predator wins at 70% of starting prey population eliminated
    - Prey wins at 65% of the map's starting aggregate resource pool consumed
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.ai.fsm import roll_intent, select_target, step_predator_solo, step_prey
from src.core.agent import Flock, Pack, PredatorAgent, PreyAgent
from src.core.combat import check_attack_triggers, resolve_attack
from src.core.grid import Grid
from src.data.loader import UnitStats


@dataclass
class TurnRecord:
    turn: int
    predator_positions: Dict[str, tuple]
    prey_positions: Dict[str, tuple]
    prey_alive_count: int
    resources_remaining: int


@dataclass
class Simulation:
    grid: Grid
    unit_stats: Dict[str, UnitStats]
    predators: List[PredatorAgent]
    prey: List[PreyAgent]
    flocks: Dict[str, Flock]
    packs: Dict[str, Pack] = field(default_factory=dict)
    turn: int = 0
    history: List[TurnRecord] = field(default_factory=list)
    starting_prey_count: int = 0
    starting_resource_total: int = 0
    winner: Optional[str] = None

    def __post_init__(self):
        self.starting_prey_count = len(self.prey)
        self.starting_resource_total = sum(self.grid.resources_remaining.values())
        for pred in self.predators:
            if pred.intent is None:
                pred.intent = roll_intent(pred.species)

    # ---- turn loop -----------------------------------------------------
    def step(self) -> None:
        self.turn += 1
        self._predator_turn()
        self._prey_turn()
        self._check_win_conditions()
        self._log_turn()

    def _predator_turn(self) -> None:
        for pred in self.predators:
            if not pred.alive:
                continue
            if pred.cooldown_remaining > 0:
                pred.cooldown_remaining -= 1

            target = select_target(self.prey, pred.pos)
            if target is None:
                continue

            new_pos = step_predator_solo(self.grid, pred, target, self.grid.height // 2) \
                if pred.pack_id is None else pred.pos  # TODO: route pack members through step_predator_pack

            move_path = [pred.pos, new_pos] if new_pos != pred.pos else [pred.pos]
            pred.pos = new_pos

            triggered_prey = [p for p in self.prey if p.alive
                               and self.grid.chebyshev_distance(pred.pos, p.pos) <= 1]
            for prey_unit in triggered_prey:
                if pred.can_attack():
                    resolve_attack(pred, prey_unit, self.unit_stats)
                    if not prey_unit.alive:
                        self._trigger_despair(prey_unit)

    def _prey_turn(self) -> None:
        for flock in self.flocks.values():
            if flock.panic_lock_turns > 0:
                flock.panic_lock_turns -= 1

        for prey_unit in self.prey:
            if not prey_unit.alive:
                continue
            flock = self.flocks[prey_unit.flock_id]
            flockmates = [p for p in self.prey if p.flock_id == flock.flock_id]
            nearest_pred = min(
                (p for p in self.predators if p.alive),
                key=lambda p: self.grid.chebyshev_distance(prey_unit.pos, p.pos),
                default=None,
            )
            nearest_pred_pos = nearest_pred.pos if nearest_pred else None

            new_pos = step_prey(self.grid, prey_unit, flock, nearest_pred_pos, flockmates)
            prey_unit.pos = new_pos

            if self.grid.tile_props(new_pos).is_resource:
                stats = self.unit_stats[prey_unit.species]
                self.grid.consume_resource(new_pos, stats.resource_yield)

    def _trigger_despair(self, attacked: PreyAgent) -> None:
        flock = self.flocks[attacked.flock_id]
        members = [p for p in self.prey if p.flock_id == flock.flock_id and p.alive]
        for m in members:
            from src.core.agent import PreyState
            m.state = PreyState.DESPAIR

    def _check_win_conditions(self) -> None:
        prey_eliminated = self.starting_prey_count - sum(1 for p in self.prey if p.alive)
        if self.starting_prey_count and prey_eliminated / self.starting_prey_count >= 0.70:
            self.winner = "predator"
            return

        resources_consumed = self.starting_resource_total - sum(self.grid.resources_remaining.values())
        if self.starting_resource_total and resources_consumed / self.starting_resource_total >= 0.65:
            self.winner = "prey"

    def _log_turn(self) -> None:
        self.history.append(TurnRecord(
            turn=self.turn,
            predator_positions={p.agent_id: p.pos for p in self.predators if p.alive},
            prey_positions={p.agent_id: p.pos for p in self.prey if p.alive},
            prey_alive_count=sum(1 for p in self.prey if p.alive),
            resources_remaining=sum(self.grid.resources_remaining.values()),
        ))

    def is_over(self) -> bool:
        return self.winner is not None
