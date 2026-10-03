"""Skirmish policy. It loads battle weights, never the wildlife file."""
from __future__ import annotations

import json
import math
import random

from src.ai.battle_search import approach_if_holding
from src.ai.learned.battle_features import FEATURE_COUNT, action_features, battle_candidates
from src.ai.learned.network import PolicyNet
from src.core.battle_match import BattleAction, BattleView
from src.root import project_root

WEIGHTS_PATH = project_root() / "config" / "policies" / "battle.json"


def _softmax(scores: list[float]) -> list[float]:
    peak = max(scores)
    shifted = [math.exp(score - peak) for score in scores]
    total = sum(shifted)
    return [value / total for value in shifted]


class BattleLearnedController:
    def __init__(self, weights: dict | None = None, *, load_default: bool = True,
                 explore: bool = False, rng: random.Random | None = None) -> None:
        if weights is None and load_default and WEIGHTS_PATH.exists():
            weights = json.loads(WEIGHTS_PATH.read_text(encoding="utf-8"))
        self.weights = None if not weights else {key: weights[key] for key in ("n_in", "n_hidden", "w1", "b1", "w2", "b2")}
        self.net = PolicyNet.from_dict(self.weights) if self.weights else None
        if self.net is not None and self.net.n_in != FEATURE_COUNT:
            raise ValueError("Battle network features do not match these weights")
        self.explore = explore
        self.rng = rng or random.Random(0)
        self.trace: list[tuple] = []

    @property
    def playable(self) -> bool:
        return self.net is not None

    def choose_action(self, view: BattleView) -> BattleAction:
        if self.net is None:
            raise RuntimeError("BattleLearnedController has no trained weights")
        actions = battle_candidates(view)
        rows = [action_features(view, destination, target) for destination, target in actions]
        scores, hiddens = self.net.scores(rows)
        probabilities = _softmax(scores)
        if self.explore:
            roll = self.rng.random()
            chosen = len(probabilities) - 1
            covered = 0.0
            for index, probability in enumerate(probabilities):
                covered += probability
                if roll <= covered:
                    chosen = index
                    break
            self.trace.append((view.actor.side, rows, hiddens, chosen, probabilities))
        else:
            chosen = max(range(len(scores)), key=lambda index: (scores[index], -index))
        destination, target = actions[chosen]
        return approach_if_holding(view, BattleAction(destination, target, "Battle policy"), "Battle policy")

    def learn(self, hunter_return: float, herd_return: float, learning_rate: float) -> None:
        if self.net is None:
            raise RuntimeError("BattleLearnedController has no trained weights")
        for side, rows, hiddens, chosen, probabilities in self.trace:
            advantage = hunter_return if side == "hunter" else herd_return
            self.net.accumulate(rows, hiddens, chosen, probabilities, advantage / max(1, len(self.trace)))
        self.net.apply(learning_rate)
        self.weights = self.net.to_dict()
        self.trace.clear()
