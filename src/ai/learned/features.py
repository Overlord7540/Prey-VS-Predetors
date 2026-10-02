"""Fixed-size features from a limited observation. One row per legal tile."""
from __future__ import annotations

from src.core.control import Observation

FEATURE_COUNT = 8


def tile_features(observation: Observation, tile: tuple[int, int]) -> list[float]:
    actor = observation.actor
    grid = observation.grid
    sight = max(1, grid.rules.sight_range)
    enemies = [agent for agent in observation.agents if agent.alive and agent.side != actor.side]
    nearest = min((grid.chebyshev_distance(tile, enemy.pos) for enemy in enemies), default=sight)
    return [
        1.0,
        (tile[0] - actor.pos[0]) / grid.height,
        (tile[1] - actor.pos[1]) / grid.width,
        grid.chebyshev_distance(tile, actor.pos) / sight,
        observation.grid.resources_remaining.get(tile, 0) / 2,
        min(observation.influence.get(tile, 0.0), sight) / sight,
        nearest / sight,
        1.0 if actor.side == "predator" else 0.0,
    ]
