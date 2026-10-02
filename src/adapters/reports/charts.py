"""Draw comparison figures from saved records. Does not run matches."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


class ComparisonChartReport:
    def write_win_rates(self, record: dict, destination: Path) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        outcomes = record["outcomes"]
        labels = list(outcomes)
        values = [outcomes[label] for label in labels]
        figure, axis = plt.subplots()
        axis.bar(labels, values, color="#1f4e79")
        axis.set_title(record.get("controller", "outcomes"))
        axis.set_ylabel("matches")
        figure.tight_layout()
        figure.savefig(path)
        plt.close(figure)
        return path

    def write_training_curve(self, values: list[float], destination: Path) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        figure, axis = plt.subplots()
        axis.plot(range(1, len(values) + 1), values, color="#1f4e79")
        axis.set_xlabel("update")
        axis.set_ylabel("value")
        axis.set_title("training")
        figure.tight_layout()
        figure.savefig(path)
        plt.close(figure)
        return path

    def write_outcome_comparison(self, comparison: dict, destination: Path) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = comparison["controllers"]
        names = [row["name"] for row in rows]
        keys = ("predator", "prey", "unfinished")
        figure, axis = plt.subplots()
        width = 0.25
        for offset, key in enumerate(keys):
            positions = [index + (offset - 1) * width for index in range(len(rows))]
            axis.bar(positions, [row["outcomes"].get(key, 0) for row in rows], width=width, label=key)
        axis.set_xticks(range(len(names)), names)
        axis.set_ylabel("matches")
        axis.set_title("Win rate by controller")
        axis.legend()
        figure.tight_layout()
        figure.savefig(path)
        plt.close(figure)
        return path

    def write_stock_comparison(self, comparison: dict, destination: Path) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = comparison["controllers"]
        names = [row["name"] for row in rows]
        positions = list(range(len(rows)))
        figure, axis = plt.subplots()
        axis.bar([index - 0.15 for index in positions], [row["mean_prey_alive"] for row in rows],
                 width=0.3, label="prey left")
        axis.bar([index + 0.15 for index in positions], [row["mean_food_consumed"] for row in rows],
                 width=0.3, label="food consumed")
        axis.set_xticks(positions, names)
        axis.set_ylabel("mean per match")
        axis.set_title("Prey left and food consumed")
        axis.legend()
        figure.tight_layout()
        figure.savefig(path)
        plt.close(figure)
        return path

    def write_battle_outcomes(self, comparison: dict, destination: Path) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = comparison["controllers"]
        names = [row["name"] for row in rows]
        keys = ("wins", "losses", "unfinished")
        figure, axis = plt.subplots()
        width = 0.25
        for offset, key in enumerate(keys):
            positions = [index + (offset - 1) * width for index in range(len(rows))]
            axis.bar(positions, [row["outcomes"].get(key, 0) for row in rows], width=width, label=key)
        axis.set_xticks(range(len(names)), names)
        axis.set_ylabel("matches")
        axis.set_title("Skirmish results against the other two")
        axis.legend()
        figure.tight_layout()
        figure.savefig(path)
        plt.close(figure)
        return path

    def write_battle_health(self, comparison: dict, destination: Path) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = comparison["controllers"]
        names = [row["name"] for row in rows]
        positions = list(range(len(rows)))
        figure, axis = plt.subplots()
        axis.bar([index - 0.15 for index in positions], [row["mean_own_hp"] for row in rows],
                 width=0.3, label="own health left")
        axis.bar([index + 0.15 for index in positions], [row["mean_opponent_hp"] for row in rows],
                 width=0.3, label="opponent health left")
        axis.set_xticks(positions, names)
        axis.set_ylabel("mean per match")
        axis.set_title("Health left in the skirmish")
        axis.legend()
        figure.tight_layout()
        figure.savefig(path)
        plt.close(figure)
        return path
