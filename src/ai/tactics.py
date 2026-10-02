"""Deterministic tactical policies over detached observations."""
from collections import deque
from src.ai.fov import visible_tiles
from src.core.control import Action
from src.core.agent import PreyState
from src.core.movement import reachable_paths


def distances(grid, starts, blocked):
    """Multi-source BFS; distances respect terrain and currently occupied tiles."""
    result = {p: 0 for p in starts if p not in blocked}
    queue = deque(result)
    while queue:
        pos = queue.popleft()
        for nxt in grid.passable_neighbors(pos):
            if nxt not in blocked and nxt not in result:
                result[nxt] = result[pos] + 1
                queue.append(nxt)
    return result


def coordinated_wolf(observation):
    actor, grid = observation.actor, observation.grid
    wolves = sorted((a for a in observation.agents
                     if a.alive and a.side == actor.side and getattr(a, "pack_id", None) == actor.pack_id),
                    key=lambda a: a.agent_id)
    prey = [a for a in observation.agents if a.alive and a.side == "prey"]
    if len(wolves) < 2 or not prey:
        return None
    occupied = {a.pos for a in observation.agents if a.alive}
    routes = {w.agent_id: distances(grid, [w.pos], occupied - {w.pos}) for w in wolves}
    slots = {p.agent_id: [tile for tile in grid.passable_neighbors(p.pos)
                         if tile not in occupied or any(w.pos == tile for w in wolves)] for p in prey}
    def cost(target):
        return sum(min((routes[w.agent_id].get(tile, 10000) for tile in slots[target.agent_id]),
                       default=10000) for w in wolves)
    target = min(prey, key=lambda p: (cost(p), p.agent_id))
    assigned = []
    for wolf in wolves:
        available = [tile for tile in slots[target.agent_id]
                     if tile not in assigned and tile in routes[wolf.agent_id]]
        if not available:
            if wolf.agent_id == actor.agent_id:
                return Action(actor.pos, "Wolf team: no reachable approach")
            continue
        # Distinct attack tiles; prefer separated approaches among equally short routes.
        goal = min(available, key=lambda tile: (routes[wolf.agent_id][tile],
                   -min((grid.chebyshev_distance(tile, other) for other in assigned), default=0), tile))
        assigned.append(goal)
        if wolf.agent_id == actor.agent_id:
            field = distances(grid, [goal], occupied - {actor.pos})
            move = min(observation.legal_destinations, key=lambda tile: (field.get(tile, 10000), tile))
            return Action(move, f"Team hunt {target.agent_id}: approach {goal}")
    return None


def explore_beyond_sight(observation):
    """Step toward tiles this animal has not seen. Remembered food is handled by foraging."""
    actor, grid = observation.actor, observation.grid
    known = set(observation.remembered or observation.visible)
    sight = grid.rules.sight_range

    def gain(tile):
        return len(visible_tiles(grid, tile, sight) - known)

    move = max(observation.legal_destinations, key=lambda tile: (gain(tile), tile[0] + tile[1], tile))
    if gain(move) == 0:
        return Action(actor.pos, "No unseen ground: wait")
    return Action(move, "Explore beyond current sight")


def forage_safely(observation):
    actor, grid = observation.actor, observation.grid
    predators = [a for a in observation.agents if a.alive and a.side == "predator"]
    occupied = {a.pos for a in observation.agents if a.alive and a.agent_id != actor.agent_id}
    food = [p for p, stock in grid.resources_remaining.items() if stock > 0]
    if not food and not predators:
        return explore_beyond_sight(observation), None
    food_distance = distances(grid, food, occupied) if food else {}
    mates = [a for a in observation.agents if a.alive and a.side == "prey"
             and a.agent_id != actor.agent_id and a.flock_id == actor.flock_id]
    # Predict one predator move, conservatively keeping current blockers in place.
    next_zones = [set([p.pos] + [tile for tile in grid.passable_neighbors(p.pos)
                               if tile not in occupied and tile != actor.pos])
                  for p in predators if p.cooldown_remaining == 0]
    if observation.unit_stats:
        next_zones = [set(reachable_paths(grid, p, observation.agents, observation.unit_stats[p.species]))
                      for p in predators if p.cooldown_remaining == 0]
    def features(tile):
        immediate = sum(p.can_attack() and grid.chebyshev_distance(tile, p.pos) <= 1
                        for p in predators)
        next_risk = sum(any(grid.chebyshev_distance(tile, pos) <= 1 for pos in zone)
                        for zone in next_zones)
        distance = min((grid.chebyshev_distance(tile, p.pos) for p in predators), default=6)
        food_steps = food_distance.get(tile, grid.width * grid.height) if food else 0
        escape = sum(n not in occupied and all(grid.chebyshev_distance(n, p.pos) > 1
                     for p in predators) for n in grid.passable_neighbors(tile))
        regroup = min((grid.chebyshev_distance(tile, m.pos) for m in mates), default=0)
        fear = 2 if actor.state != PreyState.NORMAL else 0.5
        danger = observation.influence.get(tile, 0)
        score = (-100*immediate - 30*next_risk - 2*food_steps + fear*min(distance, 6)
                 + 0.25*escape - danger - (0.5*regroup if actor.state == PreyState.DESPAIR else 0))
        return score, immediate, next_risk
    ordered = sorted(observation.legal_destinations,
                     key=lambda tile: (features(tile)[0], tile == actor.pos), reverse=True)
    here = features(actor.pos)
    if grid.resources_remaining.get(actor.pos, 0) and here[1] == 0 and here[2] == 0:
        runner = next((tile for tile in ordered if tile != actor.pos), None)
        return Action(actor.pos, "Feed safely on food underfoot"), runner
    move = ordered[0]
    runner = next((tile for tile in ordered[1:] if tile != move), None)
    _, immediate, future = features(move)
    if immediate:
        reason = "Danger unavoidable: balance escape and food"
    elif future:
        reason = "Predator may reach next turn; seek an escape route"
    elif grid.resources_remaining.get(move, 0):
        reason = "Feed outside predicted attack range"
    elif move not in food_distance:
        reason = "No reachable food: seek safer space"
    else:
        reason = "Approach food while avoiding predator reach"
    return Action(move, reason), runner
