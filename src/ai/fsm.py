"""
Behavior logic for prey (state machine) and predators (one-shot intent
+ chase/ambush/camp movement). See docs/ALGORITHMS.md for full spec.

This module is intentionally NOT a generic behavior-tree library: the
rules are specific enough (rank-scored fcost, flock-shared goals,
species-biased intent rolls) that a bespoke state machine is clearer
than shoehorning them into generic BT nodes.
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

from src.ai.pathfinding import (
    a_star,
    best_move,
    nearest_resource,
    score_moves_fcost_despair,
    score_moves_fcost_panic,
)
from src.core.movement import step_cost
from src.core.agent import Flock, Pack, PredatorAgent, PredatorIntent, PreyAgent, PreyState
from src.core.grid import Grid

Coord = Tuple[int, int]


def step_prey(
    grid: Grid,
    prey: PreyAgent,
    flock: Flock,
    nearest_predator_pos: Optional[Coord],
    flockmates: List[PreyAgent],
    occupied: Optional[set[Coord]] = None,
) -> Coord:
    """Returns the tile this prey should move to this turn."""
    occupied = occupied or set()
    # Panic tracks sighting range; despair retains its shorter escape radius.
    recovery_range = (grid.rules.panic_detection_range if prey.state == PreyState.PANIC
                      else grid.rules.despair_recovery_range)
    safe = (nearest_predator_pos is None
            or Grid.chebyshev_distance(prey.pos, nearest_predator_pos) > recovery_range)
    # Eat food underfoot before following another member's distant goal.
    if safe and grid.resources_remaining.get(prey.pos, 0) > 0:
        return prey.pos
    if prey.state == PreyState.PANIC and nearest_predator_pos:
        res = nearest_resource(grid, prey.pos)
        resource_pos = res[0] if res else None
        scores = score_moves_fcost_panic(grid, prey.pos, nearest_predator_pos, resource_pos)
        return best_move({pos: score for pos, score in scores.items() if pos not in occupied})

    if prey.state == PreyState.DESPAIR and nearest_predator_pos:
        others = [m for m in flockmates if m.agent_id != prey.agent_id and m.alive]
        nearest_mate = min(others, key=lambda m: Grid.chebyshev_distance(prey.pos, m.pos), default=None)
        mate_pos = nearest_mate.pos if nearest_mate else None
        mate_close = mate_pos is not None and Grid.chebyshev_distance(prey.pos, mate_pos) <= 2
        scores = score_moves_fcost_despair(grid, prey.pos, nearest_predator_pos, mate_pos, mate_close)
        return best_move({pos: score for pos, score in scores.items() if pos not in occupied})

    # Shared goals and emotional state are prepared by the simulation.
    if flock.shared_goal:
        path = a_star(grid, prey.pos, flock.shared_goal, blocked=occupied)
        if path and len(path) > 1:
            return path[1]
    # A flockmate may occupy the shared goal or block the route. Forage
    # locally rather than queue indefinitely behind that animal.
    alternative = nearest_resource(grid, prey.pos, blocked=occupied)
    if alternative and len(alternative[1]) > 1:
        return alternative[1][1]
    return prey.pos


# ------------------------------------------------------------ Predator ----

def roll_intent(species: str, rng: random.Random, intent_bias: Optional[str] = None) -> PredatorIntent:
    """Rolled once per match. Tiger biases CAMP, Wolf biases AMBUSH (per algorithms.md)."""
    options = [PredatorIntent.CHASE, PredatorIntent.AMBUSH, PredatorIntent.CAMP]
    weights = {
        "tiger": [1, 1, 2],   # extra weight on CAMP
        "wolf": [1, 2, 1],    # extra weight on AMBUSH
    }.get(species, [1, 1, 1])
    if intent_bias is not None:
        weights = [2 if option.name.lower() == intent_bias else 1 for option in options]
    return rng.choices(options, weights=weights, k=1)[0]


def select_target(prey_agents: List[PreyAgent], from_pos: Coord) -> Optional[PreyAgent]:
    """Closest living prey to from_pos. Recomputed every move."""
    alive = [p for p in prey_agents if p.alive]
    if not alive:
        return None
    return min(alive, key=lambda p: Grid.chebyshev_distance(from_pos, p.pos))


def step_predator_solo(grid: Grid, predator: PredatorAgent, target: PreyAgent, river_row: int,
                       occupied: Optional[set[Coord]] = None, budget: int = 1) -> Coord:
    occupied = occupied or set()
    # Attacks happen from adjacent tiles; never step onto the target.
    if Grid.chebyshev_distance(predator.pos, target.pos) <= 1:
        return predator.pos
    if predator.is_constant_chase:
        intent = PredatorIntent.CHASE
    else:
        intent = predator.intent

    if intent == PredatorIntent.CHASE:
        dest = target.pos
    elif intent == PredatorIntent.AMBUSH:
        res = nearest_resource(grid, target.pos)
        resource_pos = res[0] if res else target.pos
        dest = ((target.pos[0] + resource_pos[0]) // 2, (target.pos[1] + resource_pos[1]) // 2)
    else:  # CAMP
        if river_row < 0:
            dest = target.pos
        else:
            opposite_row = max(0, river_row - 4) if target.pos[0] > river_row else min(grid.height - 1, river_row + 4)
            dest = (opposite_row, target.pos[1])
        # A camp behind the hunter, or on a map with no river, is just a chase.
        if (Grid.chebyshev_distance(predator.pos, target.pos) < 3
                or Grid.chebyshev_distance(dest, target.pos) >= Grid.chebyshev_distance(predator.pos, target.pos)):
            dest = target.pos

    if dest in occupied:
        destinations = [pos for pos in grid.passable_neighbors(dest) if pos not in occupied]
        paths = [path for pos in destinations
                 if (path := a_star(grid, predator.pos, pos, blocked=occupied))]
        path = min(paths, key=len, default=None)
    else:
        path = a_star(grid, predator.pos, dest, blocked=occupied)
    if path and len(path) > 1:
        return _within_budget(path, max(1, budget))
    neighbors = [tile for tile in grid.passable_neighbors(predator.pos) if tile not in occupied]
    if not neighbors:
        return predator.pos
    return min(neighbors, key=lambda tile: (Grid.chebyshev_distance(tile, dest), tile))


def _within_budget(path: List[Coord], budget: int) -> Coord:
    """Walk the path until the next step would exceed the movement budget."""
    cost = 0
    landed = path[0]
    for nxt in path[1:]:
        paying = step_cost(landed, nxt)
        if cost + paying > budget:
            break
        cost += paying
        landed = nxt
    return landed


def step_predator_pack(grid: Grid, pack: Pack, wolves: List[PredatorAgent], target: PreyAgent) -> Dict[str, Coord]:
    """
    Target tile picked by whichever wolf is closest to prey; the wolf that
    actually MOVES is the one furthest from prey. A move is vetoed if it
    would put any packmate 3+ tiles from the pack's closest-to-prey wolf.
    """
    closest = min(wolves, key=lambda w: Grid.chebyshev_distance(w.pos, target.pos))
    mover = max(wolves, key=lambda w: Grid.chebyshev_distance(w.pos, target.pos))

    moves: Dict[str, Coord] = {w.agent_id: w.pos for w in wolves}
    path = a_star(grid, mover.pos, target.pos)
    if not path or len(path) <= 1:
        return moves

    candidate = path[1]
    if Grid.chebyshev_distance(candidate, closest.pos) >= 3:
        return moves  # veto: would straggle too far from the pack

    moves[mover.agent_id] = candidate
    return moves
