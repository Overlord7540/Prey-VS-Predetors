"""
Pathfinding + the fcost scoring system from docs/ALGORITHMS.md.

- bfs_shortest_path: used to find the nearest resource node for prey.
- a_star: used for predator "chase" and as the base algorithm for
  "ambush" (chase toward a derived point) and ordinary prey movement.
- score_moves_fcost: the panic/despair scoring function. Each of a prey's
  up-to-8 possible moves gets a 1-8 score for "distance from predator"
  and a 1-8 score for "distance to resource" (rank-based, not raw distance),
  summed into a single fcost. Despair mode drops the resource term and adds
  a regroup-with-flock term instead (see docs/ALGORITHMS.md).
"""
from __future__ import annotations

import heapq
from collections import deque
from typing import Dict, List, Optional, Tuple

from src.core.grid import Grid
from src.core.movement import step_cost

Coord = Tuple[int, int]


def bfs_shortest_path(grid: Grid, start: Coord, goal: Coord) -> Optional[List[Coord]]:
    if start == goal:
        return [start]
    visited = {start}
    queue = deque([[start]])
    while queue:
        path = queue.popleft()
        current = path[-1]
        for nxt in grid.passable_neighbors(current):
            if nxt in visited:
                continue
            new_path = path + [nxt]
            if nxt == goal:
                return new_path
            visited.add(nxt)
            queue.append(new_path)
    return None


def nearest_resource(grid: Grid, start: Coord, blocked: Optional[set[Coord]] = None) -> Optional[Tuple[Coord, List[Coord]]]:
    """BFS out from start, return the first resource-node tile with stock and the path to it."""
    blocked = blocked or set()
    if start in grid.resources_remaining and grid.resources_remaining[start] > 0:
        return start, [start]
    visited = {start}
    queue = deque([[start]])
    while queue:
        path = queue.popleft()
        current = path[-1]
        for nxt in grid.passable_neighbors(current):
            if nxt in visited or nxt in blocked:
                continue
            new_path = path + [nxt]
            if grid.resources_remaining.get(nxt, 0) > 0:
                return nxt, new_path
            visited.add(nxt)
            queue.append(new_path)
    return None


def a_star(grid: Grid, start: Coord, goal: Coord, blocked: Optional[set[Coord]] = None) -> Optional[List[Coord]]:
    """A* with a Manhattan heuristic. A diagonal step costs 2, a straight step costs 1."""
    blocked = blocked or set()
    if goal in blocked or not grid.is_passable(goal):
        return None
    open_set = [(0, start)]
    came_from: Dict[Coord, Coord] = {}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return list(reversed(path))

        for nxt in grid.passable_neighbors(current):
            if nxt in blocked:
                continue
            tentative_g = g_score[current] + step_cost(current, nxt)
            if tentative_g < g_score.get(nxt, float("inf")):
                came_from[nxt] = current
                g_score[nxt] = tentative_g
                dr = abs(nxt[0] - goal[0])
                dc = abs(nxt[1] - goal[1])
                f = tentative_g + dr + dc
                heapq.heappush(open_set, (f, nxt))
    return None


def _rank_scores(candidates: List[Coord], key_fn) -> Dict[Coord, int]:
    """
    Rank-based scoring per docs/ALGORITHMS.md: best candidate gets a score
    equal to len(candidates) (max 8), next best gets len-1, etc.
    key_fn(coord) -> a value where HIGHER is better for this criterion.
    """
    ordered = sorted(candidates, key=key_fn, reverse=True)
    return {coord: len(ordered) - i for i, coord in enumerate(ordered)}


def score_moves_fcost_panic(
    grid: Grid,
    prey_pos: Coord,
    predator_pos: Coord,
    nearest_resource_pos: Optional[Coord],
) -> Dict[Coord, int]:
    """PANIC state fcost: max(distance from predator) + min(distance to resource)."""
    candidates = grid.passable_neighbors(prey_pos) + [prey_pos]

    away_from_predator = _rank_scores(
        candidates, key_fn=lambda c: Grid.chebyshev_distance(c, predator_pos)
    )
    if nearest_resource_pos is not None:
        toward_resource = _rank_scores(
            candidates, key_fn=lambda c: -Grid.chebyshev_distance(c, nearest_resource_pos)
        )
    else:
        toward_resource = {c: 0 for c in candidates}

    return {c: away_from_predator[c] + toward_resource[c] for c in candidates}


def score_moves_fcost_despair(
    grid: Grid,
    prey_pos: Coord,
    predator_pos: Coord,
    nearest_flockmate_pos: Optional[Coord],
    flockmate_is_close: bool,
) -> Dict[Coord, int]:
    """
    DESPAIR state fcost: max(distance from predator) only, PLUS a regroup
    term (min distance to nearest flockmate) UNLESS that flockmate is
    already within 2 tiles.
    """
    candidates = grid.passable_neighbors(prey_pos) + [prey_pos]

    away_from_predator = _rank_scores(
        candidates, key_fn=lambda c: Grid.chebyshev_distance(c, predator_pos)
    )

    if nearest_flockmate_pos is not None and not flockmate_is_close:
        toward_flock = _rank_scores(
            candidates, key_fn=lambda c: -Grid.chebyshev_distance(c, nearest_flockmate_pos)
        )
    else:
        toward_flock = {c: 0 for c in candidates}

    return {c: away_from_predator[c] + toward_flock[c] for c in candidates}


def best_move(fcost_scores: Dict[Coord, int]) -> Coord:
    return max(fcost_scores.items(), key=lambda kv: kv[1])[0]
