"""Occupancy-aware movement ranges shared by human commands and AI."""
import heapq


def step_cost(origin, destination) -> int:
    """A straight step costs 1. A diagonal step costs 2, so it is not a free extra tile."""
    same_line = origin[0] == destination[0] or origin[1] == destination[1]
    return 1 if same_line else 2


def escape_destination(grid, actor, agents, stats, threats):
    """The reachable tile farthest from every threat. Stay put when none is safer."""
    paths = reachable_paths(grid, actor, agents, stats)
    living = [pos for pos in threats if pos is not None]

    def score(tile):
        if not living:
            return (0, tile == actor.pos)
        gaps = [grid.chebyshev_distance(tile, pos) for pos in living]
        return (min(gaps), sum(gaps), tile == actor.pos)

    return max(paths, key=score)


def reachable_paths(grid, actor, agents, stats):
    budget = stats.move_range + (2 if getattr(actor, "adrenaline", False) else 0)
    crosses_water = getattr(stats, "vulnerable_at_water_midtile", False)
    water_budget = stats.water_move_range if crosses_water else 0
    blocked = {a.pos for a in agents if a.alive and a.agent_id != actor.agent_id}
    paths = {actor.pos: (actor.pos,)}
    costs = {actor.pos: 0}
    water_used = {actor.pos: 0}
    queue = [(0, actor.pos)]
    while queue:
        cost, pos = heapq.heappop(queue)
        if cost != costs[pos]:
            continue
        for nxt in grid.neighbors(pos):
            if nxt in blocked or not _can_enter(grid, nxt, crosses_water):
                continue
            # Do not squeeze diagonally between impassable/occupied cells.
            if pos[0] != nxt[0] and pos[1] != nxt[1]:
                corners = ((pos[0], nxt[1]), (nxt[0], pos[1]))
                if any(not grid.is_passable(p) or p in blocked for p in corners):
                    continue
            river = _is_river(grid, nxt)
            spent_water = water_used[pos] + (1 if river else 0)
            if spent_water > water_budget:
                continue
            nxt_cost = cost + step_cost(pos, nxt)
            if nxt_cost > budget or nxt_cost >= costs.get(nxt, budget + 1):
                continue
            costs[nxt] = nxt_cost
            water_used[nxt] = spent_water
            paths[nxt] = paths[pos] + (nxt,)
            heapq.heappush(queue, (nxt_cost, nxt))
    return paths


def _can_enter(grid, pos, crosses_water) -> bool:
    if grid.is_passable(pos):
        return True
    return crosses_water and _is_river(grid, pos)


def _is_river(grid, pos) -> bool:
    props = grid.tile_props(pos)
    return props.is_water and not props.passable
