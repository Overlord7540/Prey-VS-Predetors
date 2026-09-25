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
from src.core.agent import Flock, Pack, PredatorAgent, PredatorIntent, PreyAgent, PreyState
from src.core.grid import Grid

Coord = Tuple[int, int]


# ---------------------------------------------------------------- Prey ----

def check_panic_trigger(
    flocks: Dict[str, Flock],
    spotter: PreyAgent,
    predators: List[PredatorAgent],
) -> Optional[PreyAgent]:
    """
    A predator was spotted. The closest prey in the flock to that predator
    enters PANIC, UNLESS the flock's panic lock is still active (n-move
    cooldown where n = flock size, set when panic last triggered).
    Tie-break: closer-to-resource wins (handled by caller passing distances).
    """
    flock = flocks[spotter.flock_id]
    if flock.panic_lock_turns > 0:
        return None
    return spotter  # caller pre-selects the closest-to-predator (with resource tiebreak)


def enter_panic(flock: Flock, prey: PreyAgent) -> None:
    prey.state = PreyState.PANIC
    flock.panic_lock_turns = len(flock.member_ids)  # "n = number of animals in flock"


def enter_despair(flock: Flock, members: List[PreyAgent]) -> None:
    """Whole flock enters DESPAIR when any member is attacked (or within 2 tiles of the attacked one)."""
    for m in members:
        m.state = PreyState.DESPAIR


def step_prey(
    grid: Grid,
    prey: PreyAgent,
    flock: Flock,
    nearest_predator_pos: Optional[Coord],
    flockmates: List[PreyAgent],
) -> Coord:
    """Returns the tile this prey should move to this turn."""
    if prey.state == PreyState.PANIC and nearest_predator_pos:
        res = nearest_resource(grid, prey.pos)
        resource_pos = res[0] if res else None
        scores = score_moves_fcost_panic(grid, prey.pos, nearest_predator_pos, resource_pos)
        return best_move(scores)

    if prey.state == PreyState.DESPAIR and nearest_predator_pos:
        others = [m for m in flockmates if m.agent_id != prey.agent_id and m.alive]
        nearest_mate = min(others, key=lambda m: Grid.chebyshev_distance(prey.pos, m.pos), default=None)
        mate_pos = nearest_mate.pos if nearest_mate else None
        mate_close = mate_pos is not None and Grid.chebyshev_distance(prey.pos, mate_pos) <= 2
        scores = score_moves_fcost_despair(grid, prey.pos, nearest_predator_pos, mate_pos, mate_close)
        return best_move(scores)

    # NORMAL: follow the flock's shared goal (set once, held until resource depleted)
    if flock.shared_goal is None:
        res = nearest_resource(grid, prey.pos)
        if res:
            flock.shared_goal = res[0]
    if flock.shared_goal:
        path = a_star(grid, prey.pos, flock.shared_goal)
        if path and len(path) > 1:
            return path[1]
    return prey.pos


# ------------------------------------------------------------ Predator ----

def roll_intent(species: str) -> PredatorIntent:
    """Rolled once per match. Tiger biases CAMP, Wolf biases AMBUSH (per algorithms.md)."""
    options = [PredatorIntent.CHASE, PredatorIntent.AMBUSH, PredatorIntent.CAMP]
    weights = {
        "tiger": [1, 1, 2],   # extra weight on CAMP
        "wolf": [1, 2, 1],    # extra weight on AMBUSH
    }.get(species, [1, 1, 1])
    return random.choices(options, weights=weights, k=1)[0]


def select_target(prey_agents: List[PreyAgent], from_pos: Coord) -> Optional[PreyAgent]:
    """Closest living prey to from_pos. Recomputed every move."""
    alive = [p for p in prey_agents if p.alive]
    if not alive:
        return None
    return min(alive, key=lambda p: Grid.chebyshev_distance(from_pos, p.pos))


def step_predator_solo(grid: Grid, predator: PredatorAgent, target: PreyAgent, river_row: int) -> Coord:
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
        opposite_row = max(0, river_row - 4) if target.pos[0] > river_row else min(grid.height - 1, river_row + 4)
        dest = (opposite_row, target.pos[1])
        if Grid.chebyshev_distance(predator.pos, target.pos) < 3:
            dest = target.pos  # close enough: switch to chase-style closing

    path = a_star(grid, predator.pos, dest)
    return path[1] if path and len(path) > 1 else predator.pos


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
