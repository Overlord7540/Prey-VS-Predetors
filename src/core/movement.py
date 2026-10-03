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
    # Meadow animals wade. A duel fighter has no water budget and still treats the river as a wall.
    wades = hasattr(stats, "water_move_range")
    swift = _buffalo(actor, stats)
    blocked = {a.pos for a in agents if a.alive and a.agent_id != actor.agent_id}
    paths = {actor.pos: (actor.pos,)}
    costs = {actor.pos: 0}
    queue = [(0, actor.pos)]
    while queue:
        cost, pos = heapq.heappop(queue)
        if cost != costs[pos]:
            continue
        for nxt in grid.neighbors(pos):
            if nxt in blocked or not _can_enter(grid, nxt, wades):
                continue
            # Do not squeeze diagonally between impassable/occupied cells.
            if pos[0] != nxt[0] and pos[1] != nxt[1]:
                corners = ((pos[0], nxt[1]), (nxt[0], pos[1]))
                if any(not grid.is_passable(p) or p in blocked for p in corners):
                    continue
            nxt_cost = cost + _step_cost(grid, pos, nxt, swift)
            # Spend the whole move to wade one tile. Otherwise a heron could not enter water at all.
            if (nxt_cost > budget and cost == 0 and not swift
                    and grid.tile_props(nxt).is_water and step_cost(pos, nxt) == 1):
                nxt_cost = budget
            if nxt_cost > budget or nxt_cost >= costs.get(nxt, budget + 1):
                continue
            costs[nxt] = nxt_cost
            paths[nxt] = paths[pos] + (nxt,)
            heapq.heappush(queue, (nxt_cost, nxt))
    return paths


def _buffalo(actor, stats) -> bool:
    return getattr(actor, "species", None) == "buffalo" or getattr(stats, "name", None) == "buffalo"


def _step_cost(grid, origin, destination, swift: bool) -> int:
    """Water costs one extra movement point. A buffalo pays the normal step."""
    paying = step_cost(origin, destination)
    if grid.tile_props(destination).is_water and not swift:
        paying += 1
    return paying


def _can_enter(grid, pos, wades: bool) -> bool:
    if grid.is_passable(pos):
        return True
    return wades and grid.is_enterable(pos)
