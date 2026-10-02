"""Seeded match batches. Returns a record; persistence and charts stay outside."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict
import json

from src.ai.catalog import wildlife_catalog
from src.core.scenario import build_default_scenario
from src.root import project_root


class BatchEvaluation:
    def run(self, start_seed: int = 0, matches: int = 100, max_rounds: int = 300,
            controller: str = "tactical") -> dict:
        if matches < 1 or max_rounds < 1:
            raise ValueError("matches and max_rounds must be positive")
        catalog = wildlife_catalog()
        controller_type = type(catalog.create(controller))
        results = []
        sim = None
        for seed in range(start_seed, start_seed + matches):
            sim = build_default_scenario(seed=seed)
            sim.default_controller = controller_type()
            for _ in range(max_rounds):
                if sim.is_over():
                    break
                sim.step()
            results.append({
                "seed": seed,
                "winner": sim.winner or "unfinished",
                "rounds": sim.turn,
                "prey_alive": sum(prey.alive for prey in sim.prey),
                "food_consumed": sim.starting_resource_total - sum(sim.grid.resources_remaining.values()),
            })
        config_dir = project_root() / "config"
        return {
            "controller": controller_type.__name__,
            "start_seed": start_seed,
            "max_rounds": max_rounds,
            "rules": asdict(sim.grid.rules),
            "configuration": {
                path.name: json.loads(path.read_text(encoding="utf-8"))
                for path in sorted(config_dir.glob("*.json"))
            },
            "outcomes": dict(Counter(result["winner"] for result in results)),
            "matches": results,
        }

    def compare(self, start_seed: int = 0, matches: int = 4, max_rounds: int = 40,
                names: tuple[str, ...] = ("baseline", "tactical", "learned")) -> dict:
        controllers = []
        for name in names:
            record = self.run(start_seed, matches, max_rounds, name)
            played = record["matches"]
            controllers.append({
                "name": name,
                "outcomes": record["outcomes"],
                "mean_prey_alive": sum(match["prey_alive"] for match in played) / len(played),
                "mean_food_consumed": sum(match["food_consumed"] for match in played) / len(played),
                "matches": played,
            })
        return {
            "start_seed": start_seed,
            "matches": matches,
            "max_rounds": max_rounds,
            "controllers": controllers,
        }
