"""Play-time corrections for a score that would walk past a bite or into one."""
from __future__ import annotations

from src.ai.fov import visible_tiles
from src.ai.tactics import distances, explore_beyond_sight
from src.core.control import Observation


def sensible_destination(observation: Observation, chosen: tuple[int, int]) -> tuple[int, int]:
    """Hunters close on prey they can see. Herd animals do not step into a ready bite."""
    actor = observation.actor
    grid = observation.grid
    legal = list(observation.legal_destinations) or [actor.pos]
    if chosen not in legal:
        chosen = actor.pos
    enemies = [agent for agent in observation.agents if agent.alive and agent.side != actor.side]
    if actor.side == "predator":
        prey = [agent for agent in enemies if not getattr(agent, "escape_guard", False)]
        bites = [tile for tile in legal if any(grid.chebyshev_distance(tile, unit.pos) == 1 for unit in prey)]
        if bites and chosen not in bites:
            def bite_key(tile: tuple[int, int]) -> tuple:
                victim = min((unit for unit in prey if grid.chebyshev_distance(tile, unit.pos) == 1),
                             key=lambda unit: (unit.hp, unit.agent_id))
                return (victim.hp, grid.chebyshev_distance(actor.pos, tile), tile)
            return min(bites, key=bite_key)
        if not prey:
            return _search_if_blind(observation, legal, chosen, actor.pos)
        nearest = min(prey, key=lambda unit: (grid.chebyshev_distance(actor.pos, unit.pos), unit.agent_id))
        blocked = {agent.pos for agent in observation.agents if agent.alive and agent.agent_id != actor.agent_id}
        goals = [tile for tile in grid.passable_neighbors(nearest.pos) if tile not in blocked] or [nearest.pos]
        field = distances(grid, goals, blocked)
        best = min(legal, key=lambda tile: (field.get(tile, 10000), grid.chebyshev_distance(tile, nearest.pos), tile))
        if field.get(best, 10000) < field.get(chosen, 10000):
            return best
        return chosen

    hunters = [agent for agent in enemies if getattr(agent, "can_attack", lambda: False)()]

    def exposed(tile: tuple[int, int]) -> bool:
        return any(grid.chebyshev_distance(tile, hunter.pos) <= 1 for hunter in hunters)

    safe = [tile for tile in legal if not exposed(tile)]
    if safe and exposed(chosen):
        def flee_key(tile: tuple[int, int]) -> tuple:
            distance = min((grid.chebyshev_distance(tile, hunter.pos) for hunter in hunters), default=0)
            return (-distance, -grid.resources_remaining.get(tile, 0), tile)
        return min(safe, key=flee_key)
    if not hunters:
        return chosen
    nearest = min(hunters, key=lambda hunter: (grid.chebyshev_distance(actor.pos, hunter.pos), hunter.agent_id))

    def gap(tile: tuple[int, int]) -> int:
        return grid.chebyshev_distance(tile, nearest.pos)

    if gap(chosen) >= gap(actor.pos):
        return chosen
    safer = [tile for tile in legal if gap(tile) >= gap(actor.pos)]
    if not safer:
        return chosen
    return max(safer, key=lambda tile: (gap(tile), grid.resources_remaining.get(tile, 0), tile))


def _search_if_blind(observation: Observation, legal: list, chosen: tuple[int, int], origin: tuple[int, int]) -> tuple[int, int]:
    """A hunter who sees nobody should not pace ground it has already seen."""
    step = explore_beyond_sight(observation)
    if step.destination == origin or step.destination not in legal:
        return chosen
    grid = observation.grid
    known = set(observation.remembered or observation.visible)
    sight = grid.rules.sight_range

    def gain(tile: tuple[int, int]) -> int:
        return len(visible_tiles(grid, tile, sight) - known)

    if gain(chosen) > 0:
        return chosen
    return step.destination
