"""Offline REINFORCE for the skirmish policy. It does not train the wildlife network."""
from __future__ import annotations

import json
import random
from pathlib import Path

from src.ai.learned.battle_controller import WEIGHTS_PATH, BattleLearnedController
from src.ai.learned.battle_features import FEATURE_COUNT
from src.ai.learned.network import PolicyNet
from src.core.battle import build_battle
from src.core.battle_match import BattleMatch


class BattleTrainer:
    def run(self, episodes: int = 12, max_rounds: int = 8, seed: int = 1,
            learning_rate: float = 0.08) -> dict:
        if episodes < 1 or max_rounds < 1:
            raise ValueError("episodes and max_rounds must be positive")
        rng = random.Random(seed)
        net = PolicyNet(FEATURE_COUNT, 8, random.Random(seed))
        curve = []
        baseline = 0.0
        for episode in range(episodes):
            controller = BattleLearnedController(weights=net.to_dict(), explore=True, rng=rng)
            match = BattleMatch(build_battle(), controller, seed=seed + episode, max_rounds=max_rounds)
            starting = {unit.name: unit.hp for unit in match.combatants}
            steps = 0
            while not match.finished and steps < max_rounds * 8:
                match.step()
                steps += 1
            hunter_return = _return_for_hunter(match, starting)
            advantage = hunter_return - baseline
            baseline = 0.9 * baseline + 0.1 * hunter_return
            controller.learn(advantage, -advantage, learning_rate)
            net = controller.net
            curve.append(hunter_return)
        record = net.to_dict()
        record["domain"] = "battle"
        record["training"] = {
            "seed": seed,
            "episodes": episodes,
            "max_rounds": max_rounds,
            "learning_rate": learning_rate,
            "curve": curve,
        }
        return record

    def save(self, record: dict, path: Path = WEIGHTS_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record), encoding="utf-8")
        return path


def _return_for_hunter(match: BattleMatch, starting: dict[str, int]) -> float:
    def fraction_remaining(side: str) -> float:
        total = sum(starting[unit.name] for unit in match.combatants if unit.side == side)
        left = sum(unit.hp for unit in match.combatants if unit.side == side)
        return left / max(1, total)

    if match.winner == "hunter":
        outcome = 1.0
    elif match.winner == "herd":
        outcome = -1.0
    else:
        outcome = 0.0
    return (1.0 - fraction_remaining("herd")) - (1.0 - fraction_remaining("hunter")) + outcome
