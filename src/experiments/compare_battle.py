"""Compare skirmish rules, search, and the battle network, then write the figures."""
import argparse
import json
from pathlib import Path

from src.adapters.reports.charts import ComparisonChartReport
from src.ai.learned.battle_controller import WEIGHTS_PATH
from src.application.battle_evaluation import BattleEvaluation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--matches", type=int, default=4)
    parser.add_argument("--max-rounds", type=int, default=8)
    parser.add_argument("--output", type=Path, default=Path("results/battle_comparison.json"))
    parser.add_argument("--figures", type=Path, default=Path("results/figures"))
    args = parser.parse_args()
    comparison = BattleEvaluation().compare(args.seed, args.matches, args.max_rounds)
    if WEIGHTS_PATH.exists():
        trained = json.loads(WEIGHTS_PATH.read_text(encoding="utf-8"))
        comparison["training_curve"] = trained.get("training", {}).get("curve", [])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(comparison), encoding="utf-8")
    report = ComparisonChartReport()
    report.write_battle_outcomes(comparison, args.figures / "battle_wins.png")
    report.write_battle_health(comparison, args.figures / "battle_health.png")
    if comparison.get("training_curve"):
        report.write_training_curve(comparison["training_curve"], args.figures / "battle_training.png")
    print(json.dumps({row["name"]: row["outcomes"] for row in comparison["controllers"]}, indent=2))


if __name__ == "__main__":
    main()
