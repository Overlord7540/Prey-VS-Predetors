"""Offline REINFORCE for the wildlife policy. No window and no charts."""
from __future__ import annotations

import json
import random
from pathlib import Path

from src.ai.learned.controller import WEIGHTS_PATH, LearnedController
from src.ai.learned.features import FEATURE_COUNT
from src.ai.learned.network import PolicyNet
from src.core.scenario import build_default_scenario


class WildlifeTrainer:
    def run(self, episodes: int = 12, max_rounds: int = 20, seed: int = 1,
            learning_rate: float = 0.08, scenario_name: str = "riverlands",
            resume: bool = False) -> dict:
        if episodes < 1 or max_rounds < 1:
            raise ValueError("episodes and max_rounds must be positive")
        rng = random.Random(seed)
        prior = []
        if resume and WEIGHTS_PATH.exists():
            saved = json.loads(WEIGHTS_PATH.read_text(encoding="utf-8"))
            net = PolicyNet.from_dict(saved)
            prior = list(saved.get("training", {}).get("curve") or [])
        else:
            net = PolicyNet(FEATURE_COUNT, 8, random.Random(seed))
        curve = []
        baseline = 0.0
        for episode in range(episodes):
            controller = LearnedController(weights=net.to_dict(), explore=True, rng=rng)
            match = build_default_scenario(
                seed=seed + len(prior) + episode, scenario_name=scenario_name)
            match.default_controller = controller
            for _ in range(max_rounds):
                if match.is_over():
                    break
                match.step()
            predator_return = _return_for_predator(match)
            advantage = predator_return - baseline
            baseline = 0.9 * baseline + 0.1 * predator_return
            controller.learn(advantage, -advantage, learning_rate)
            net = controller.net
            curve.append(predator_return)
        record = net.to_dict()
        record["training"] = {
            "seed": seed,
            "episodes": len(prior) + episodes,
            "added_episodes": episodes,
            "resumed": bool(prior),
            "max_rounds": max_rounds,
            "scenario": scenario_name,
            "learning_rate": learning_rate,
            "curve": prior + curve,
        }
        return record

    def save(self, record: dict, path: Path = WEIGHTS_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record), encoding="utf-8")
        return path


def _return_for_predator(match) -> float:
    killed = match.starting_prey_count - sum(prey.alive for prey in match.prey)
    eaten = match.starting_resource_total - sum(match.grid.resources_remaining.values())
    predator_progress = killed / max(1, match.starting_prey_count)
    prey_progress = eaten / max(1, match.starting_resource_total)
    if match.winner == "predator":
        outcome = 1.0
    elif match.winner == "prey":
        outcome = -1.0
    else:
        outcome = 0.0
    return predator_progress - prey_progress + outcome
