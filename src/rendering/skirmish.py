"""A skirmish shown through the wildlife board. Watch, or command one side."""
from __future__ import annotations

from types import SimpleNamespace

from src.ai.battle_rules import RuleBattleController
from src.ai.battle_search import SearchBattleController
from src.ai.learned.battle_controller import BattleLearnedController
from src.core.battle import build_battle
from src.core.battle_match import COVER, BattleAction, BattleMatch
from src.core.control import Action

CONTROLLERS = {
    "rules": RuleBattleController,
    "search": SearchBattleController,
    "learned": BattleLearnedController,
}


class _Piece:
    def __init__(self, combatant):
        self.agent_id = combatant.name
        self.battle_name = combatant.name
        self.battle_side = combatant.side
        self.species = combatant.body
        self.side = "prey" if combatant.side == "herd" else "predator"
        self.pos = combatant.pos
        self.hp = combatant.hp
        self.max_hp = combatant.hp
        self.alive = True
        self.intent = SimpleNamespace(name=combatant.name)
        self.state = SimpleNamespace(name="Herd")
        self.flock_id = ""
        self.is_constant_chase = False
        self.cooldown_remaining = 0
        self.attack_used = False
        self.resting_this_round = False
        self.pack_id = None

    def sync(self, combatant) -> None:
        self.pos = combatant.pos
        self.hp = combatant.hp
        self.alive = combatant.alive

    def can_attack(self) -> bool:
        return False


class _Shown:
    def __init__(self, kind, pos, damage):
        self.kind = kind
        self.pos = pos
        self.damage = damage


class SkirmishMatch:
    kind = "skirmish"

    def __init__(self, controller_name: str, seed: int | None, player_side: str | None = None,
                 battle_name: str = "skirmish"):
        self.controller_name = controller_name
        self.player_battle_side = player_side
        self.battle = BattleMatch(build_battle(battle_name), CONTROLLERS[controller_name](), seed=seed, max_rounds=30)
        pieces = [_Piece(unit) for unit in self.battle.combatants]
        self._by_name = {piece.agent_id: piece for piece in pieces}
        self.predators = [piece for piece in pieces if piece.battle_side == "hunter"]
        self.prey = [piece for piece in pieces if piece.battle_side == "herd"]
        self.grid = self.battle.grid
        self.player_side = {"hunter": "predator", "herd": "prey"}.get(player_side)
        self.human_turn = False
        self.pending_player_ids: set[str] = set()
        self.decision_reasons: dict[str, str] = {}
        self.events: list[_Shown] = []
        self.active_agent_id = self.predators[0].agent_id
        self.winner = None
        self._offer()

    @property
    def turn(self) -> int:
        return self.battle.round

    @property
    def phase(self) -> str:
        side = "Tiger pack" if self.battle._phase == 0 else "Jackals"
        return f"{self.active_agent_id} · {side}"

    def is_over(self) -> bool:
        return self.battle.finished

    def step(self) -> None:
        if self.human_turn or self.battle.finished:
            return
        before = len(self.battle.events)
        self.battle.step()
        self._show_since(before)
        self._offer()

    def step_action(self) -> None:
        self.step()

    def observe(self, agent_id: str):
        actor = self.battle.fighter(agent_id)
        view = self.battle._view(actor)
        return SimpleNamespace(actor=SimpleNamespace(pos=actor.pos), legal_destinations=view.legal_destinations, view=view)

    def attack_targets(self, agent_id: str, pos):
        view = self.observe(agent_id).view
        return [self._by_name[name] for destination, name in view.attacks if destination == pos]

    def attack_preview(self, agent_id: str, target_id: str, pos):
        actor = self.battle.fighter(agent_id)
        target = self.battle.fighter(target_id)
        low = max(1, actor.damage - actor.damage_spread)
        high = actor.damage + actor.damage_spread
        if self.grid.tiles[target.pos[0]][target.pos[1]] == "chokepoint":
            low, high = max(1, low - COVER), max(1, high - COVER)
        return low, high, max(0, target.hp - high), max(0, target.hp - low)

    def submit_player_action(self, agent_id: str, action: Action) -> None:
        if not self.human_turn or agent_id not in self.pending_player_ids:
            raise ValueError("That fighter cannot act")
        view = self.observe(agent_id).view
        if action.destination not in view.legal_destinations:
            raise ValueError("Choose a highlighted destination")
        target = action.target_id if action.kind == "attack" else None
        if action.kind == "attack" and (action.destination, target) not in view.attacks:
            raise ValueError("That attack is not legal")
        before = len(self.battle.events)
        self.battle.apply(BattleAction(action.destination, target, "Your order"))
        self._show_since(before)
        self._offer()

    def _show_since(self, before: int) -> None:
        for unit in self.battle.combatants:
            self._by_name[unit.name].sync(unit)
        self.events = []
        for event in self.battle.events[before:]:
            self.active_agent_id = event["actor"]
            if event["kind"] == "move":
                self.events.append(_Shown("step", event["destination"], 0))
            elif event["kind"] == "attack":
                target = self._by_name[event["target"]]
                kind = "kill" if not target.alive else "hit"
                self.events.append(_Shown(kind, target.pos, event["damage"]))
        self.winner = self.battle.winner

    def _offer(self) -> None:
        actor = None if self.battle.finished else self.battle.pending_actor()
        if actor is not None and actor.side == self.player_battle_side:
            self.human_turn = True
            self.pending_player_ids = {actor.name}
            self.active_agent_id = actor.name
            return
        self.human_turn = False
        self.pending_player_ids = set()
