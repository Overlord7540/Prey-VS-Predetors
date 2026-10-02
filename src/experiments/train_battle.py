"""Train and save the skirmish policy: python -m src.experiments.train_battle."""
import argparse

from src.application.battle_training import BattleTrainer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=12)
    parser.add_argument("--max-rounds", type=int, default=8)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    trainer = BattleTrainer()
    record = trainer.run(args.episodes, args.max_rounds, args.seed)
    path = trainer.save(record)
    print(f"Saved {path} after {args.episodes} episodes")


if __name__ == "__main__":
    main()
