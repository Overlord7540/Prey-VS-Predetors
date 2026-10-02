"""Trim a detached observation to what one animal can see, then add enemy influence."""
from __future__ import annotations

from dataclasses import replace

from src.ai.fov import visible_tiles
from src.ai.influence_map import InfluenceMap
from src.core.control import Observation


def limit_awareness(observation: Observation, known: set[tuple[int, int]] | None = None) -> Observation:
    grid = observation.grid
    actor = observation.actor
    stats = (observation.unit_stats or {}).get(actor.species)
    sight = stats.sight_range if stats is not None and stats.sight_range else grid.rules.sight_range
    visible = visible_tiles(grid, actor.pos, sight)
    remembered = set(known or ()) | visible
    agents = tuple(agent for agent in observation.agents
                   if agent.agent_id == actor.agent_id or (agent.alive and agent.pos in visible))
    for pos in list(grid.resources_remaining):
        if pos not in remembered:
            del grid.resources_remaining[pos]
    flock = observation.flock
    if flock is not None and flock.shared_goal not in remembered:
        flock.shared_goal = None
    enemies = [agent.pos for agent in agents if agent.alive and agent.side != actor.side]
    influence = InfluenceMap(grid.width, grid.height).radiate(enemies, sight, visible)
    return replace(
        observation,
        agents=agents,
        visible=tuple(sorted(visible)),
        remembered=tuple(sorted(remembered)),
        influence=influence,
    )
