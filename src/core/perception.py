"""Simulation-owned fear transitions and shared resource goals."""
from src.core.agent import PreyState
from src.ai.pathfinding import nearest_resource


def update_flocks(grid, flocks, prey_agents, predators, unit_stats=None):
    for flock in flocks.values():
        if flock.panic_lock_turns > 0:
            flock.panic_lock_turns -= 1
            continue  # A lock of n blocks the next n full prey phases.
        candidates = []
        for prey in prey_agents:
            if not prey.alive or prey.flock_id != flock.flock_id or prey.state != PreyState.NORMAL:
                continue
            distance = min((grid.chebyshev_distance(prey.pos, pred.pos)
                            for pred in predators if pred.alive), default=float("inf"))
            stats = None if unit_stats is None else unit_stats.get(prey.species)
            panic_range = stats.panic_range if stats is not None and stats.panic_range else grid.rules.panic_detection_range
            if distance <= panic_range:
                resource = nearest_resource(grid, prey.pos)
                resource_distance = len(resource[1]) - 1 if resource else float("inf")
                candidates.append((distance, resource_distance, prey.agent_id, prey))
        if candidates:
            chosen = min(candidates, key=lambda item: item[:3])[3]
            chosen.state = PreyState.PANIC
            flock.panic_lock_turns = len(flock.member_ids)


def prepare_prey(grid, prey, flock, predators):
    nearest = min((p for p in predators if p.alive),
                  key=lambda p: grid.chebyshev_distance(prey.pos, p.pos), default=None)
    distance = grid.chebyshev_distance(prey.pos, nearest.pos) if nearest else float("inf")
    radius = (grid.rules.panic_detection_range if prey.state == PreyState.PANIC
              else grid.rules.despair_recovery_range)
    safe = distance > radius
    if safe:
        prey.state = PreyState.NORMAL
    if safe and grid.resources_remaining.get(prey.pos, 0) > 0:
        return
    if prey.state != PreyState.NORMAL:
        return
    if grid.resources_remaining.get(flock.shared_goal, 0) <= 0:
        flock.shared_goal = None
    if flock.shared_goal is None:
        resource = nearest_resource(grid, prey.pos)
        if resource:
            flock.shared_goal = resource[0]
