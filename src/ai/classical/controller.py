"""One table player. It picks the legal tile with the highest saved score."""
from __future__ import annotations

import json

from src.ai.classical.models import BUILDERS, _direction, _situation
from src.ai.learned.features import tile_features
from src.ai.sense import sensible_destination
from src.core.control import Action, Observation
from src.root import project_root

RECORD_PATH = project_root() / "config" / "policies" / "classical.json"

LABELS = {
    "logistic": "Logistic regression",
    "tree": "Decision tree",
    "forest": "Random forest",
    "bayes": "Naive Bayes",
    "markov": "Markov model",
}


def _worth_returning(observation: Observation, back: tuple[int, int], other: tuple[int, int]) -> bool:
    """Keep a reverse step when it is the one that bites, or the richer food tile."""
    actor = observation.actor
    grid = observation.grid
    if actor.side == "prey":
        return grid.resources_remaining.get(back, 0) > grid.resources_remaining.get(other, 0)
    enemies = [agent for agent in observation.agents if agent.alive and agent.side != actor.side]

    def strikes(tile: tuple[int, int]) -> bool:
        return any(grid.chebyshev_distance(tile, enemy.pos) <= 1 for enemy in enemies)

    return strikes(back) and not strikes(other)


def load_record() -> dict | None:
    if not RECORD_PATH.exists():
        return None
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


class TableController:
    def __init__(self, name: str) -> None:
        self.name = name
        self.model = None
        self._last: dict[str, tuple[int, int]] = {}
        self._left: dict[str, tuple[int, int]] = {}
        record = load_record()
        payload = None if record is None else record.get("weights", {}).get(name)
        if payload is not None:
            self.model = BUILDERS[name].from_dict(payload)

    @property
    def playable(self) -> bool:
        return True

    def choose_action(self, observation: Observation) -> Action:
        self.runner_up = None
        legal = list(observation.legal_destinations) or [observation.actor.pos]
        if self.model is None:
            return Action(legal[0], f"{LABELS[self.name]} is not trained yet", "auto")
        rows = [tile_features(observation, tile) for tile in legal]
        if self.name == "markov":
            scores = [self.model.score(row, self._last.get(str(_situation(row)), (0, 0))) for row in rows]
        else:
            scores = [self.model.score(row) for row in rows]
        chosen = max(range(len(scores)), key=lambda index: (scores[index], -index))
        order = sorted(range(len(scores)), key=lambda index: (scores[index], -index), reverse=True)
        self.runner_up = legal[order[1]] if len(order) > 1 and order[1] != chosen else None
        chosen = self._avoid_pacing(observation, legal, chosen)
        picked = sensible_destination(observation, legal[chosen])
        if picked != legal[chosen]:
            self.runner_up = legal[chosen]
            chosen = legal.index(picked)
        if self.name == "markov":
            self._last[str(_situation(rows[chosen]))] = _direction(rows[chosen])
        self._left[observation.actor.agent_id] = observation.actor.pos
        return Action(legal[chosen], LABELS[self.name], "auto")

    def _avoid_pacing(self, observation: Observation, legal: list, chosen: int) -> int:
        """A memoryless score will walk back onto the tile it just left. Take the next tile."""
        actor = observation.actor
        previous = self._left.get(actor.agent_id)
        picked = legal[chosen]
        other = self.runner_up
        if previous is None or picked != previous or picked == actor.pos or other in (None, picked):
            return chosen
        if _worth_returning(observation, picked, other):
            return chosen
        self.runner_up = picked
        return legal.index(other)
