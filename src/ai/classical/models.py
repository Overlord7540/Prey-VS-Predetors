"""Small table models. Each one scores one tile; the caller picks the highest score."""
from __future__ import annotations

import math
import random


def _sigmoid(value: float) -> float:
    if value > 20:
        return 1.0
    if value < -20:
        return 0.0
    return 1.0 / (1.0 + math.exp(-value))


def _dot(weights: list[float], row: list[float]) -> float:
    return sum(weight * feature for weight, feature in zip(weights, row))


class LogisticModel:
    def __init__(self, weights: list[float] | None = None, bias: float = 0.0) -> None:
        self.weights = weights or []
        self.bias = bias

    def fit(self, examples: list[tuple[list[float], int]], seed: int = 0) -> None:
        width = len(examples[0][0])
        self.weights = [0.0] * width
        self.bias = 0.0
        rate = 0.15
        for _ in range(25):
            for row, label in examples:
                error = _sigmoid(_dot(self.weights, row) + self.bias) - label
                for index, feature in enumerate(row):
                    self.weights[index] -= rate * error * feature
                self.bias -= rate * error

    def score(self, row: list[float]) -> float:
        return _dot(self.weights, row) + self.bias

    def to_dict(self) -> dict:
        return {"weights": self.weights, "bias": self.bias}

    @classmethod
    def from_dict(cls, payload: dict) -> "LogisticModel":
        return cls(list(payload["weights"]), float(payload["bias"]))


class BayesModel:
    def __init__(self, payload: dict | None = None) -> None:
        self.means = payload["means"] if payload else [[], []]
        self.variances = payload["variances"] if payload else [[], []]
        self.prior = payload["prior"] if payload else [0.5, 0.5]

    def fit(self, examples: list[tuple[list[float], int]], seed: int = 0) -> None:
        width = len(examples[0][0])
        grouped = [[], []]
        for row, label in examples:
            grouped[label].append(row)
        self.means, self.variances = [], []
        for rows in grouped:
            count = max(1, len(rows))
            means = [sum(row[index] for row in rows) / count for index in range(width)]
            variances = []
            for index, mean in enumerate(means):
                moment = sum((row[index] - mean) ** 2 for row in rows) / count
                variances.append(max(0.01, moment))
            self.means.append(means)
            self.variances.append(variances)
        total = max(1, len(examples))
        self.prior = [len(grouped[0]) / total, len(grouped[1]) / total]

    def score(self, row: list[float]) -> float:
        return self._log_prob(row, 1) - self._log_prob(row, 0)

    def _log_prob(self, row: list[float], label: int) -> float:
        total = math.log(max(1e-6, self.prior[label]))
        for feature, mean, variance in zip(row, self.means[label], self.variances[label]):
            total += -0.5 * math.log(2 * math.pi * variance)
            total += -((feature - mean) ** 2) / (2 * variance)
        return total

    def to_dict(self) -> dict:
        return {"means": self.means, "variances": self.variances, "prior": self.prior}

    @classmethod
    def from_dict(cls, payload: dict) -> "BayesModel":
        return cls(payload)


def _entropy(labels: list[int]) -> float:
    count = len(labels)
    if count == 0:
        return 0.0
    share = sum(labels) / count
    total = 0.0
    for probability in (share, 1 - share):
        if 0 < probability < 1:
            total -= probability * math.log2(probability)
    return total


def _grow(examples: list[tuple[list[float], int]], depth: int, features: list[int], rng: random.Random) -> dict:
    labels = [label for _, label in examples]
    leaf = {"p": sum(labels) / max(1, len(labels))}
    if depth == 0 or len(examples) < 8 or len(set(labels)) < 2:
        return leaf
    parent = _entropy(labels)
    best = None
    for feature in features:
        values = sorted({row[feature] for row, _ in examples})
        if len(values) < 2:
            continue
        cuts = [(values[index] + values[index + 1]) / 2 for index in range(0, len(values) - 1, max(1, len(values) // 6))]
        for threshold in cuts[:6]:
            left = [item for item in examples if item[0][feature] <= threshold]
            right = [item for item in examples if item[0][feature] > threshold]
            if len(left) < 4 or len(right) < 4:
                continue
            gain = parent - (len(left) * _entropy([label for _, label in left]) + len(right) * _entropy([label for _, label in right])) / len(examples)
            if best is None or gain > best[0]:
                best = (gain, feature, threshold, left, right)
    if best is None or best[0] <= 0:
        return leaf
    _, feature, threshold, left, right = best
    return {
        "feature": feature,
        "threshold": threshold,
        "left": _grow(left, depth - 1, features, rng),
        "right": _grow(right, depth - 1, features, rng),
    }


def _tree_score(node: dict, row: list[float]) -> float:
    if "feature" not in node:
        return float(node["p"])
    branch = "left" if row[node["feature"]] <= node["threshold"] else "right"
    return _tree_score(node[branch], row)


class TreeModel:
    def __init__(self, tree: dict | None = None) -> None:
        self.tree = tree or {"p": 0.5}

    def fit(self, examples: list[tuple[list[float], int]], seed: int = 0) -> None:
        width = len(examples[0][0])
        self.tree = _grow(examples, 3, list(range(width)), random.Random(seed))

    def score(self, row: list[float]) -> float:
        return _tree_score(self.tree, row)

    def to_dict(self) -> dict:
        return {"tree": self.tree}

    @classmethod
    def from_dict(cls, payload: dict) -> "TreeModel":
        return cls(payload["tree"])


class ForestModel:
    def __init__(self, trees: list[dict] | None = None) -> None:
        self.trees = trees or []

    def fit(self, examples: list[tuple[list[float], int]], seed: int = 0) -> None:
        rng = random.Random(seed)
        width = len(examples[0][0])
        self.trees = []
        for _ in range(5):
            sample = [examples[rng.randrange(len(examples))] for _ in examples]
            features = rng.sample(range(width), k=min(4, width))
            self.trees.append(_grow(sample, 3, features, rng))

    def score(self, row: list[float]) -> float:
        if not self.trees:
            return 0.0
        return sum(_tree_score(tree, row) for tree in self.trees) / len(self.trees)

    def to_dict(self) -> dict:
        return {"trees": self.trees}

    @classmethod
    def from_dict(cls, payload: dict) -> "ForestModel":
        return cls(payload["trees"])


def _direction(row: list[float]) -> tuple[int, int]:
    def sign(value: float) -> int:
        if abs(value) < 0.02:
            return 0
        return 1 if value > 0 else -1
    return sign(row[1]), sign(row[2])


def _situation(row: list[float]) -> tuple[int, int, int, int]:
    def band(value: float) -> int:
        if value < 0.34:
            return 0
        return 1 if value < 0.67 else 2
    return (1 if row[4] > 0 else 0, band(row[6]), band(row[5]), 1 if row[7] > 0.5 else 0)


class MarkovModel:
    """Next step depends on the current situation and the previous step."""

    def __init__(self, counts: dict | None = None) -> None:
        self.counts = counts or {}

    def fit(self, samples: list[tuple[list[list[float]], int]], seed: int = 0) -> None:
        previous: dict[str, tuple[int, int]] = {}
        self.counts = {}
        for rows, chosen in samples:
            row = rows[chosen]
            actor = str(_situation(row))
            key = str((actor, previous.get(actor, (0, 0))))
            direction = str(_direction(row))
            bucket = self.counts.setdefault(key, {})
            bucket[direction] = bucket.get(direction, 0) + 1
            previous[actor] = _direction(row)

    def score(self, row: list[float], previous: tuple[int, int] = (0, 0)) -> float:
        key = str((str(_situation(row)), previous))
        bucket = self.counts.get(key, {})
        return float(bucket.get(str(_direction(row)), 0))

    def to_dict(self) -> dict:
        return {"counts": self.counts}

    @classmethod
    def from_dict(cls, payload: dict) -> "MarkovModel":
        return cls(payload.get("counts", {}))


BUILDERS = {
    "logistic": LogisticModel,
    "tree": TreeModel,
    "forest": ForestModel,
    "bayes": BayesModel,
    "markov": MarkovModel,
}
