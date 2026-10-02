"""Train the five table players: python -m src.experiments.train_classical."""
import argparse

from src.application.classical_training import train_table_players, training_lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matches", type=int, default=4)
    parser.add_argument("--max-rounds", type=int, default=12)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--scenario", choices=("riverlands", "basin"), default="riverlands")
    args = parser.parse_args()
    train_table_players(args.matches, args.max_rounds, args.seed, args.scenario)
    for line in training_lines():
        print(line)


if __name__ == "__main__":
    main()
