"""Copy the tactical player's moves, then measure whether each table player learned them."""
from __future__ import annotations

import json

from src.ai.classical.controller import LABELS, RECORD_PATH
from src.ai.classical.models import BUILDERS
from src.ai.learned.controller import WEIGHTS_PATH
from src.ai.learned.features import tile_features
from src.ai.policies import TacticalController
from src.core.scenario import build_default_scenario


class _Recorder:
    def __init__(self) -> None:
        self.samples: list[tuple[list[list[float]], int]] = []
        self.inner = TacticalController()

    def choose_action(self, observation):
        action = self.inner.choose_action(observation)
        legal = list(observation.legal_destinations) or [observation.actor.pos]
        rows = [tile_features(observation, tile) for tile in legal]
        chosen = legal.index(action.destination) if action.destination in legal else 0
        self.samples.append((rows, chosen))
        return action


def _examples(samples: list[tuple[list[list[float]], int]]) -> list[tuple[list[float], int]]:
    rows = []
    for features, chosen in samples:
        for index, row in enumerate(features):
            rows.append((row, 1 if index == chosen else 0))
    return rows


def _accuracy(model, samples, name: str) -> float:
    if not samples:
        return 0.0
    hits = 0
    for rows, chosen in samples:
        if name == "markov":
            scores = [model.score(row) for row in rows]
        else:
            scores = [model.score(row) for row in rows]
        pick = max(range(len(scores)), key=lambda index: (scores[index], -index))
        hits += pick == chosen
    return hits / len(samples)


def _chance(samples) -> float:
    if not samples:
        return 0.0
    return sum(1 / len(rows) for rows, _ in samples) / len(samples)


def _neural_sentence() -> str:
    if not WEIGHTS_PATH.exists():
        return "Neural policy: no saved weights yet."
    payload = json.loads(WEIGHTS_PATH.read_text(encoding="utf-8"))
    curve = payload.get("training", {}).get("curve") or []
    if len(curve) < 2:
        return "Neural policy: weights are saved, but the training scores were not kept, so improvement cannot be shown."
    start, end = curve[0], curve[-1]
    if end > start + 0.05:
        change = "ended higher than it started"
    elif end < start - 0.05:
        change = "ended lower than it started"
    else:
        change = "ended about where it started"
    sentence = f"Neural policy {change}: {start:.2f} at the first episode, {end:.2f} after {len(curve)} episodes."
    evaluation = payload.get("training", {}).get("evaluation")
    if evaluation:
        before = evaluation["before"].get("predator", 0)
        after = evaluation["after"].get("predator", 0)
        matches = evaluation.get("matches", 0)
        sentence += f" On the same {matches} seeds, hunter wins went from {before} to {after}."
    return sentence


def lift_phrase(row: dict) -> str:
    gap = row["test_accuracy"] - row["chance"]
    if gap <= 0.02:
        return "not better than guessing a legal tile yet"
    if gap < 0.10:
        return "only a small lift over guessing"
    return "clearly better than guessing a legal tile"


def verdict(name: str) -> str:
    record = load_training_record()
    row = None if record is None else record.get("models", {}).get(name)
    if row is None:
        return "Not trained yet. Open Training and press 1."
    return (
        f"Matches Tactical on {row['test_accuracy']:.0%} of new moves. "
        f"Guessing is about {row['chance']:.0%}. {lift_phrase(row).capitalize()}."
    )


def training_lines(record: dict | None = None) -> list[str]:
    """Plain sentences. The menu shows these; it does not read logs."""
    record = load_training_record() if record is None else record
    lines = [
        "Three original players: Greedy, Tactical, and the Neural policy.",
        "Greedy takes the nearest gain. Tactical uses sight, influence, and the pack.",
        "The table players copy Tactical's moves, then are checked on moves they did not train on.",
        _neural_sentence(),
    ]
    if record is None:
        lines.append("Table players are not trained yet. Press 1 on this page.")
        return lines
    lines.append(
        f"Trained on {record['train_decisions']} moves from {record['matches']} matches. "
        f"Checked on {record['test_decisions']} new moves."
    )
    for name, label in LABELS.items():
        row = record["models"][name]
        play = record.get("play", {}).get(name)
        played = ""
        if play:
            total = sum(play.values())
            played = f" With both sides using it, the hunters won {play.get('predator', 0)} of {total}."
        lines.append(
            f"{label}: same tile as Tactical on {row['test_accuracy']:.0%} of new moves. "
            f"Guessing would be about {row['chance']:.0%}. This is {lift_phrase(row)}.{played}"
        )
    return lines


def load_training_record() -> dict | None:
    if not RECORD_PATH.exists():
        return None
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


def measure_table_players(samples: list, seed: int = 1) -> dict:
    """Score each model on the last fifth of the recorded moves."""
    if len(samples) < 4:
        raise RuntimeError("Not enough tactical moves to train")
    holdout = max(1, len(samples) // 5)
    train_samples, test_samples = samples[:-holdout], samples[-holdout:]
    examples = _examples(train_samples)
    weights = {}
    measured = {}
    chance = _chance(test_samples)
    for offset, name in enumerate(LABELS):
        model = BUILDERS[name]()
        if name == "markov":
            model.fit(train_samples, seed + offset)
        else:
            model.fit(examples, seed + offset)
        accuracy = _accuracy(model, test_samples, name)
        weights[name] = model.to_dict()
        measured[name] = {
            "test_accuracy": round(accuracy, 4),
            "chance": round(chance, 4),
            "improved": accuracy > chance + 0.02,
        }
    return {
        "train_decisions": len(train_samples),
        "test_decisions": len(test_samples),
        "models": measured,
        "weights": weights,
    }


def grade_table_play(start_seed: int = 0, matches: int = 4, max_rounds: int = 40) -> dict:
    """Win counts when both sides use the copy. This does not change the copy."""
    from src.application.evaluation import BatchEvaluation

    evaluation = BatchEvaluation()
    return {
        name: evaluation.run(start_seed, matches, max_rounds, name)["outcomes"]
        for name in LABELS
    }


def train_table_players(matches: int = 4, max_rounds: int = 12, seed: int = 1,
                        scenario_name: str = "riverlands") -> dict:
    if matches < 1 or max_rounds < 1:
        raise ValueError("matches and max_rounds must be positive")
    samples = []
    for index in range(matches):
        recorder = _Recorder()
        match = build_default_scenario(seed=seed + index, scenario_name=scenario_name)
        match.default_controller = recorder
        for _ in range(max_rounds):
            if match.is_over():
                break
            match.step()
        samples.extend(recorder.samples)
    record = measure_table_players(samples, seed)
    record.update({"matches": matches, "max_rounds": max_rounds, "seed": seed, "scenario": scenario_name})
    record["play"] = grade_table_play()
    RECORD_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECORD_PATH.write_text(json.dumps(record), encoding="utf-8")
    return record
