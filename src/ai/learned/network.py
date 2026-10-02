"""A tiny tanh network. Inference and the REINFORCE step stay in this module."""
from __future__ import annotations

import math
import random


class PolicyNet:
    def __init__(self, n_in: int, n_hidden: int, rng: random.Random):
        scale = 0.3
        self.n_in = n_in
        self.n_hidden = n_hidden
        self.w1 = [[rng.uniform(-scale, scale) for _ in range(n_in)] for _ in range(n_hidden)]
        self.b1 = [0.0 for _ in range(n_hidden)]
        self.w2 = [rng.uniform(-scale, scale) for _ in range(n_hidden)]
        self.b2 = 0.0
        self._clear()

    def _clear(self) -> None:
        self._gw1 = [[0.0 for _ in range(self.n_in)] for _ in range(self.n_hidden)]
        self._gb1 = [0.0 for _ in range(self.n_hidden)]
        self._gw2 = [0.0 for _ in range(self.n_hidden)]
        self._gb2 = 0.0

    def scores(self, rows: list[list[float]]) -> tuple[list[float], list[list[float]]]:
        values = []
        hiddens = []
        for features in rows:
            hidden = []
            for weights, bias in zip(self.w1, self.b1):
                hidden.append(math.tanh(bias + sum(weight * feature for weight, feature in zip(weights, features))))
            values.append(self.b2 + sum(weight * hidden_value for weight, hidden_value in zip(self.w2, hidden)))
            hiddens.append(hidden)
        return values, hiddens

    def accumulate(self, rows: list[list[float]], hiddens: list[list[float]],
                   chosen: int, probabilities: list[float], scale: float) -> None:
        for index, (features, hidden) in enumerate(zip(rows, hiddens)):
            coefficient = scale * ((1.0 - probabilities[index]) if index == chosen else -probabilities[index])
            self._gb2 += coefficient
            for hidden_index, hidden_value in enumerate(hidden):
                self._gw2[hidden_index] += coefficient * hidden_value
                activation = coefficient * self.w2[hidden_index] * (1.0 - hidden_value * hidden_value)
                self._gb1[hidden_index] += activation
                for feature_index, feature in enumerate(features):
                    self._gw1[hidden_index][feature_index] += activation * feature

    def apply(self, learning_rate: float) -> None:
        def clip(value: float) -> float:
            return max(-5.0, min(5.0, value))

        for hidden_index in range(self.n_hidden):
            for feature_index in range(self.n_in):
                self.w1[hidden_index][feature_index] += learning_rate * clip(self._gw1[hidden_index][feature_index])
            self.b1[hidden_index] += learning_rate * clip(self._gb1[hidden_index])
            self.w2[hidden_index] += learning_rate * clip(self._gw2[hidden_index])
        self.b2 += learning_rate * clip(self._gb2)
        self._clear()

    def to_dict(self) -> dict:
        return {
            "n_in": self.n_in,
            "n_hidden": self.n_hidden,
            "w1": self.w1,
            "b1": self.b1,
            "w2": self.w2,
            "b2": self.b2,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> "PolicyNet":
        net = cls(raw["n_in"], raw["n_hidden"], random.Random(0))
        net.w1 = raw["w1"]
        net.b1 = raw["b1"]
        net.w2 = raw["w2"]
        net.b2 = raw["b2"]
        return net
