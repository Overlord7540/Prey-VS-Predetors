"""
Master turn loop. Zero Pygame imports - fully headless and pytest-able.

Turn structure (see current docs/GDD.md):
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
from typing import Dict, Iterator, List, Optional

from src.ai.awareness import limit_awareness
from src.ai.fsm import roll_intent
from src.ai.policies import TacticalController
from src.ai.review import note_decision
from src.core.control import Action, Controller, Observation
from src.core.perception import prepare_prey, update_flocks
from copy import deepcopy
import random
from src.core.agent import Flock, Pack, PredatorAgent, PreyAgent, PreyState
from src.core.combat import WATER_EXPOSURE, resolve_attack, damage_range
from src.core.movement import escape_destination, reachable_paths
from src.core.grid import Grid
from src.data.loader import UnitStats


from src.core.records import SimulationEvent, TurnRecord, ActionRecord
from src.core.turns import round_sequence


@dataclass
class Simulation:
    grid: Grid
    unit_stats: Dict[str, UnitStats]
    predators: List[PredatorAgent]
    prey: List[PreyAgent]
    flocks: Dict[str, Flock]
    packs: Dict[str, Pack] = field(default_factory=dict)
    seed: Optional[int] = None
    rng: Optional[random.Random] = field(default=None, repr=False)
    controllers: Dict[str, Controller] = field(default_factory=dict, repr=False)
    default_controller: Controller = field(default_factory=TacticalController, repr=False)
    decision_reasons: Dict[str, str] = field(default_factory=dict, init=False)
    known_tiles: Dict[str, set] = field(default_factory=dict, init=False, repr=False)
    player_side: Optional[str] = None
    human_turn: bool = field(default=False, init=False)
    pending_player_ids: set[str] = field(default_factory=set, init=False)
    turn: int = 0
    history: List[TurnRecord] = field(default_factory=list)
    starting_prey_count: int = 0
    starting_resource_total: int = 0
    winner: Optional[str] = None
    events: List[SimulationEvent] = field(default_factory=list)
    phase: str = field(default="Ready", init=False)
    active_agent_id: Optional[str] = field(default=None, init=False)
    last_action: Optional[ActionRecord] = field(default=None, init=False)
    _round_actions: Optional[Iterator] = field(default=None, init=False, repr=False)


    def __post_init__(self):
        if self.player_side not in (None, "predator", "prey"):
            raise ValueError("Invalid player side")
        if self.rng is None:
            self.rng = random.Random(self.seed)
        ids = [a.agent_id for a in self.predators + self.prey]
        if len(ids) != len(set(ids)):
            raise ValueError("Agent IDs must be unique")
        occupied = set()
        for agent in self.predators + self.prey:
            if not agent.alive:
                continue
            if not self.grid.is_passable(agent.pos) or agent.pos in occupied:
                raise ValueError(f"Invalid or occupied spawn tile for {agent.agent_id}: {agent.pos}")
            occupied.add(agent.pos)
        self.starting_prey_count = len(self.prey)
        self.starting_resource_total = sum(self.grid.resources_remaining.values())
        self.briefing = None
        for pred in self.predators:
            if pred.intent is None:
                pred.intent = roll_intent(pred.species, self.rng, self.unit_stats[pred.species].intent_bias)

    # ---- turn loop -----------------------------------------------------
    def step(self) -> None:
        """Finish one round, including a round partially shown in detailed mode."""
        if self.is_over() or self.human_turn:
            return
        round_events = []
        while True:
            self.step_action()
            round_events.extend(self.events)
            if self._round_actions is None or self.human_turn:
                break
        self.events = round_events

    def step_action(self) -> None:
        """Advance one visible phase or unit action without changing game rules."""
        if self.is_over() or self.human_turn:
            return
        self.events.clear()
        if self._round_actions is None:
            self._round_actions = round_sequence(self)
        next(self._round_actions)
        if self.phase == "Round complete":
            self._round_actions = None

    def submit_player_action(self, agent_id: str, action: Action) -> None:
        """Commit one legal command; rejected commands do not spend the action."""
        if not self.human_turn or agent_id not in self.pending_player_ids:
            raise ValueError("This unit cannot act now")
        observation = self.observe(agent_id)
        if (not isinstance(action, Action) or not isinstance(action.destination, tuple)
                or len(action.destination) != 2
                or any(type(v) is not int for v in action.destination)
                or action.destination not in observation.legal_destinations):
            raise ValueError("Choose a highlighted destination")
        actor = next(a for a in self.predators + self.prey if a.agent_id == agent_id)
        self.validate_command(actor, action)
        self.events.clear()
        execute = self._act_predator if actor.side == "predator" else self._act_prey
        self._show_action(actor, lambda unit: execute(unit, action))
        self.pending_player_ids.remove(agent_id)

    def end_player_turn(self) -> None:
        """Unused units wait without attacking or feeding."""
        if not self.human_turn:
            raise ValueError("It is not your turn")
        events = []
        for actor in self.predators + self.prey:
            if actor.alive and actor.agent_id in self.pending_player_ids:
                self.submit_player_action(actor.agent_id, Action(actor.pos, kind="wait"))
                events.extend(self.events)
        self.pending_player_ids.clear()
        self.human_turn = False
        self.events = events

    def _show_action(self, agent, action):
        self.active_agent_id = agent.agent_id
        before = agent.pos
        state_before = agent.state if agent.side == "prey" else None
        food_before = sum(self.grid.resources_remaining.values())
        hp_before = sum(p.hp for p in self.prey if p.alive)
        action(agent)
        self.last_action = ActionRecord(
            actor=agent.agent_id, side=agent.side, before=before, after=agent.pos,
            state_before=state_before.name if state_before else None,
            state_after=agent.state.name if agent.side == "prey" else None,
            food_consumed=food_before - sum(self.grid.resources_remaining.values()),
            damage=hp_before - sum(p.hp for p in self.prey if p.alive),
            kills=sum(e.kind == "kill" for e in self.events), alive=agent.alive,
        )

    def _begin_combat_round(self) -> None:
        for pred in self.predators:
            pred.begin_round()

    def _predator_turn(self) -> None:
        self._begin_combat_round()
        for pred in self.predators:
            if pred.alive:
                self._act_predator(pred)

    def _act_predator(self, pred, action=None) -> None:
        action = action or self._choose_action(pred)
        self.decision_reasons[pred.agent_id] = action.reason or "Player/controller command"
        self._move_agent(pred, action.destination)

        if action.kind == "attack":
            target = next((p for p in self.attack_targets(pred.agent_id, pred.pos)
                           if p.agent_id == action.target_id), None)
            if target:
                self._attack(pred, target)

    def _attack(self, pred, prey_unit) -> bool:
        if self.grid.chebyshev_distance(pred.pos, prey_unit.pos) != 1:
            return False
        exposure = WATER_EXPOSURE if self._exposed_in_river(prey_unit) else 0
        damage = resolve_attack(pred, prey_unit, self.unit_stats, self.rng, exposure)
        if damage <= 0:
            return False
        struck = prey_unit.pos
        self._trigger_despair(prey_unit)
        self.events.append(SimulationEvent(
            self.turn, "kill" if not prey_unit.alive else "hit",
            struck, pred.agent_id, prey_unit.agent_id, damage))
        if prey_unit.alive and prey_unit.escape_guard:
            self._bolt(prey_unit)
        return True

    def _bolt(self, prey_unit) -> None:
        threats = [predator.pos for predator in self.predators if predator.alive]
        destination = escape_destination(
            self.grid, prey_unit, self.predators + self.prey,
            self.unit_stats[prey_unit.species], threats)
        if destination == prey_unit.pos:
            self.decision_reasons[prey_unit.agent_id] = "Struck, but no open tile is farther away"
            return
        self._move_agent(prey_unit, destination)
        self.decision_reasons[prey_unit.agent_id] = "Struck and still standing: bolt out of reach"
        self.events.append(SimulationEvent(
            self.turn, "fled", prey_unit.pos, prey_unit.agent_id, prey_unit.agent_id))

    def _tick_flocks(self) -> None:
        update_flocks(self.grid, self.flocks, self.prey, self.predators, self.unit_stats)

    def _prey_turn(self) -> None:
        self._tick_flocks()
        for prey_unit in self.prey:
            if prey_unit.alive:
                self._act_prey(prey_unit)

    def _exposed_in_river(self, prey_unit) -> bool:
        stats = self.unit_stats[prey_unit.species]
        tile = self.grid.tiles[prey_unit.pos[0]][prey_unit.pos[1]]
        return stats.vulnerable_at_water_midtile and tile == "river"

    def _act_prey(self, prey_unit, action=None) -> None:
        stats = self.unit_stats[prey_unit.species]
        if stats.recovery_hp_per_turn and prey_unit.hp < prey_unit.max_hp:
            prey_unit.hp = min(prey_unit.max_hp, prey_unit.hp + stats.recovery_hp_per_turn)
        flock = self.flocks[prey_unit.flock_id]
        prepare_prey(self.grid, prey_unit, flock, self.predators)
        action = action or self._choose_action(prey_unit)
        self.decision_reasons[prey_unit.agent_id] = action.reason or "Player/controller command"
        new_pos = action.destination
        old_pos = prey_unit.pos
        self._move_agent(prey_unit, new_pos)
        new_pos = prey_unit.pos
        prey_unit.adrenaline = False
        prey_unit.escape_guard = False
        prey_unit.adrenaline_cooldown = max(0, prey_unit.adrenaline_cooldown - 1)
        if action.kind in ("auto", "feed") and self.grid.tile_props(new_pos).is_resource:
            stats = self.unit_stats[prey_unit.species]
            consumed = self.grid.consume_resource(new_pos, stats.resource_yield)
            if consumed and self.grid.resources_remaining[new_pos] == 0:
                self.events.append(SimulationEvent(
                    self.turn, "depleted", new_pos, prey_unit.agent_id))

    def observe(self, agent_id: str) -> Observation:
        """Detached snapshot limited to what this animal can see."""
        agents = self.predators + self.prey
        actor = next((a for a in agents if a.agent_id == agent_id and a.alive), None)
        if actor is None:
            raise ValueError(f"Unknown or dead agent: {agent_id}")
        legal = tuple(self.movement_paths(actor))
        flock = self.flocks.get(actor.flock_id) if actor.side == "prey" else None
        snapshot = deepcopy(Observation(self.turn, actor, tuple(agents), self.grid, flock, legal, self.unit_stats))
        return limit_awareness(snapshot, self.known_tiles.get(actor.agent_id))

    def _choose_action(self, actor) -> Action:
        observation = self.observe(actor.agent_id)
        self.known_tiles.setdefault(actor.agent_id, set()).update(observation.visible)
        controller = self.controllers.get(actor.agent_id,
                     self.controllers.get(actor.side, self.default_controller))
        action = controller.choose_action(observation)
        # Validate against live state, not a snapshot a controller might modify.
        if not isinstance(action, Action):
            raise TypeError("Controllers must return an Action")
        destination = action.destination
        if (not isinstance(destination, tuple) or len(destination) != 2
                or any(type(value) is not int for value in destination)):
            raise ValueError("Action destination must be two integer coordinates")
        # Legacy controllers may request only a destination; select a target explicitly.
        if actor.side == "predator" and action.kind == "auto":
            destination = action.destination if action.destination in observation.legal_destinations else actor.pos
            targets = self.attack_targets(actor.agent_id, destination)
            target = min(targets, key=lambda p: (p.hp, p.agent_id), default=None)
            action = Action(destination, action.reason, "attack" if target else "wait",
                            target.agent_id if target else None)
        self.briefing = note_decision(controller, observation, action)
        return action

    def movement_paths(self, actor):
        return reachable_paths(self.grid, actor, self.predators + self.prey, self.unit_stats[actor.species])

    def attack_targets(self, agent_id, destination):
        actor = next((a for a in self.predators if a.agent_id == agent_id and a.alive), None)
        if actor is None or not actor.can_attack():
            return []
        return [p for p in self.prey if p.alive and not p.escape_guard
                and self.grid.chebyshev_distance(destination, p.pos) == 1]

    def attack_preview(self, agent_id, target_id, destination):
        actor = next(a for a in self.predators if a.agent_id == agent_id)
        target = next((p for p in self.attack_targets(agent_id, destination) if p.agent_id == target_id), None)
        if target is None or destination not in self.movement_paths(actor):
            raise ValueError("Target is not in attack range")
        low, high = damage_range(actor, self.unit_stats)
        stats = self.unit_stats[actor.species]
        if not stats.one_shot_kill and target.hp == target.max_hp and target.hp > 1:
            high = min(high, target.hp - 1)
            low = min(low, high)
        return low, high, max(0, target.hp-high), max(0, target.hp-low)

    def validate_command(self, actor, action):
        if action.kind not in ("auto", "wait", "feed", "attack"):
            raise ValueError("Unknown action")
        if action.kind == "attack":
            if action.target_id not in {p.agent_id for p in self.attack_targets(actor.agent_id, action.destination)}:
                raise ValueError("Choose an available adjacent target")
        elif action.target_id is not None:
            raise ValueError("Only attack commands have targets")
        if action.kind == "feed" and (actor.side != "prey" or not self.grid.resources_remaining.get(action.destination, 0)):
            raise ValueError("Choose a tile with food")

    def occupied_positions(self, moving_agent=None) -> set[tuple[int, int]]:
        """Live positions at this instant; sequential moves reserve tiles immediately."""
        return {agent.pos for agent in self.predators + self.prey
                if agent.alive and agent is not moving_agent}

    def _move_agent(self, agent, destination) -> None:
        if destination in self.movement_paths(agent):
            agent.pos = destination

    def _trigger_despair(self, attacked: PreyAgent) -> None:
        flock = self.flocks[attacked.flock_id]
        members = [p for p in self.prey if p.flock_id == flock.flock_id and p.alive]
        for m in members:
            m.state = PreyState.DESPAIR

    def _check_win_conditions(self) -> None:
        prey_eliminated = self.starting_prey_count - sum(1 for p in self.prey if p.alive)
        if self.starting_prey_count and prey_eliminated / self.starting_prey_count >= self.grid.rules.predator_win_prey_elimination_pct:
            self.winner = "predator"
            return

        resources_consumed = self.starting_resource_total - sum(self.grid.resources_remaining.values())
        if self.starting_resource_total and resources_consumed / self.starting_resource_total >= self.grid.rules.prey_win_resource_pool_pct:
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
