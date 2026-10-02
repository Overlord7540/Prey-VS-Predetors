"""Wildlife policy. It scores legal tiles from the limited observation."""
from __future__ import annotations

import json
import math
import random

from src.ai.learned.features import FEATURE_COUNT, tile_features
from src.ai.learned.network import PolicyNet
from src.ai.sense import sensible_destination
from src.ai.tactics import explore_beyond_sight
from src.core.control import Action, Observation
from src.root import project_root

WEIGHTS_PATH = project_root() / "config" / "policies" / "wildlife.json"


def softmax(scores: list[float]) -> list[float]:
    peak = max(scores)
    shifted = [math.exp(score - peak) for score in scores]
    total = sum(shifted)
    return [value / total for value in shifted]


class LearnedController:
    def __init__(self, weights: dict | None = None, *, load_default: bool = True,
                 explore: bool = False, rng: random.Random | None = None) -> None:
        if weights is None and load_default and WEIGHTS_PATH.exists():
            weights = json.loads(WEIGHTS_PATH.read_text(encoding="utf-8"))
        self.weights = None if not weights else {key: weights[key] for key in ("n_in", "n_hidden", "w1", "b1", "w2", "b2")}
        self.net = PolicyNet.from_dict(self.weights) if self.weights else None
        self.explore = explore
        self.rng = rng or random.Random(0)
        self.trace: list[tuple[str, list[list[float]], list[list[float]], int, list[float]]] = []

    @property
    def playable(self) -> bool:
        return self.net is not None

    def choose_action(self, observation: Observation) -> Action:
        if self.net is None:
            raise RuntimeError("LearnedController has no trained weights")
        legal = list(observation.legal_destinations) or [observation.actor.pos]
        rows = [tile_features(observation, tile) for tile in legal]
        if len(rows[0]) != FEATURE_COUNT or self.net.n_in != FEATURE_COUNT:
            raise ValueError("Observation features do not match the trained network")
        scores, hiddens = self.net.scores(rows)
        probabilities = softmax(scores)
        if self.explore:
            roll = self.rng.random()
            chosen = len(probabilities) - 1
            covered = 0.0
            for index, probability in enumerate(probabilities):
                covered += probability
                if roll <= covered:
                    chosen = index
                    break
            self.trace.append((observation.actor.side, rows, hiddens, chosen, probabilities))
        else:
            chosen = max(range(len(scores)), key=lambda index: (scores[index], -index))
        order = sorted(range(len(scores)), key=lambda index: (scores[index], -index), reverse=True)
        self.runner_up = legal[order[1]] if len(order) > 1 and order[1] != chosen else None
        if not self.explore:
            picked = sensible_destination(observation, legal[chosen])
            if picked != legal[chosen]:
                self.runner_up = legal[chosen]
                chosen = legal.index(picked)
            chosen = self._step_if_idle(observation, legal, chosen)
        return Action(legal[chosen], "Learned policy", "auto")

    def _step_if_idle(self, observation: Observation, legal: list, chosen: int) -> int:
        """A near-tie for standing still, with nothing in sight, is not a plan. Look further."""
        actor = observation.actor
        if legal[chosen] != actor.pos:
            return chosen
        visible = set(observation.visible)
        if any(agent.alive and agent.side != actor.side and agent.pos in visible for agent in observation.agents):
            return chosen
        if actor.side == "prey" and observation.grid.resources_remaining.get(actor.pos, 0):
            return chosen
        if actor.side == "prey":
            food = [pos for pos, stock in observation.grid.resources_remaining.items() if stock]
            if food:
                nearest = min(food, key=lambda pos: observation.grid.chebyshev_distance(actor.pos, pos))
                here = observation.grid.chebyshev_distance(actor.pos, nearest)
                closer = [tile for tile in legal
                          if observation.grid.chebyshev_distance(tile, nearest) < here]
                if closer:
                    self.runner_up = actor.pos
                    best = min(closer, key=lambda tile: (observation.grid.chebyshev_distance(tile, nearest), tile))
                    return legal.index(best)
        step = explore_beyond_sight(observation)
        if step.destination == actor.pos or step.destination not in legal:
            return chosen
        self.runner_up = actor.pos
        return legal.index(step.destination)

    def learn(self, predator_return: float, prey_return: float, learning_rate: float) -> None:
        if self.net is None:
            raise RuntimeError("LearnedController has no trained weights")
        for side, rows, hiddens, chosen, probabilities in self.trace:
            advantage = predator_return if side == "predator" else prey_return
            self.net.accumulate(rows, hiddens, chosen, probabilities, advantage / max(1, len(self.trace)))
        self.net.apply(learning_rate)
        self.weights = self.net.to_dict()
        self.trace.clear()
