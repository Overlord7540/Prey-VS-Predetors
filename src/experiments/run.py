"""Repeatable headless evaluation: python -m src.experiments.run."""
import argparse
import json
from pathlib import Path

from src.adapters.persistence.result_store import ResultStore
from src.ai.catalog import wildlife_catalog
from src.application.evaluation import BatchEvaluation


def run_batch(start_seed=0, matches=100, max_rounds=300, controller="tactical"):
    return BatchEvaluation().run(start_seed, matches, max_rounds, controller)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--matches", type=int, default=100)
    parser.add_argument("--max-rounds", type=int, default=300)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--controller", choices=wildlife_catalog().playable_names(), default="tactical")
    args = parser.parse_args()
    result = run_batch(args.seed, args.matches, args.max_rounds, args.controller)
    if args.output:
        ResultStore().save(result, args.output)
    print(json.dumps(result["outcomes"], indent=2))


if __name__ == "__main__":
    main()
