"""Train and save the wildlife policy: python -m src.experiments.train."""
import argparse

from src.application.training import WildlifeTrainer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=12)
    parser.add_argument("--max-rounds", type=int, default=20)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    from src.application.evaluation import BatchEvaluation
    trainer = WildlifeTrainer()
    before = BatchEvaluation().run(0, 4, 40, "learned")["outcomes"] if args.resume else None
    record = trainer.run(args.episodes, args.max_rounds, args.seed, resume=args.resume)
    path = trainer.save(record)
    if before is not None:
        after = BatchEvaluation().run(0, 4, 40, "learned")["outcomes"]
        record["training"]["evaluation"] = {"matches": 4, "max_rounds": 40, "before": before, "after": after}
        path = trainer.save(record)
    print(f"Saved {path} after {args.episodes} episodes")


if __name__ == "__main__":
    main()
