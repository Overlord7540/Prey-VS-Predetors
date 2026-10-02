"""Existing hand-authored AI behind the interchangeable controller contract."""
from src.core.control import Action, Observation
from src.ai.fsm import select_target, step_predator_solo, step_prey


class RuleBasedController:
    playable = True

    def choose_action(self, observation: Observation) -> Action:
        actor = observation.actor
        grid = observation.grid
        occupied = {a.pos for a in observation.agents if a.alive and a.agent_id != actor.agent_id}
        if actor.side == "predator":
            target = select_target([a for a in observation.agents if a.side == "prey" and a.alive], actor.pos)
            if target is None:
                from src.ai.tactics import explore_beyond_sight
                found = explore_beyond_sight(observation)
                if found.destination != actor.pos:
                    return Action(found.destination, "No prey in sight: keep searching")
                return Action(actor.pos, "No prey in sight")
            stats = (observation.unit_stats or {}).get(actor.species)
            budget = stats.move_range if stats is not None else 1
            if getattr(actor, "adrenaline", False):
                budget += 2
            return Action(step_predator_solo(grid, actor, target, grid.river_row, occupied, budget))
        predators = [a for a in observation.agents if a.side == "predator" and a.alive]
        nearest = min(predators, key=lambda p: grid.chebyshev_distance(actor.pos, p.pos), default=None)
        flockmates = [a for a in observation.agents if a.side == "prey" and a.flock_id == actor.flock_id]
        return Action(step_prey(grid, actor, observation.flock,
                                nearest.pos if nearest else None, flockmates, occupied))


class TacticalController(RuleBasedController):
    """Team hunting and risk-aware foraging; baseline remains interchangeable."""

    def __init__(self):
        self._tracks = {}

    def _take_tile(self, tiles, key):
        ordered = sorted(tiles, key=key)
        self.runner_up = ordered[1] if len(ordered) > 1 and ordered[1] != ordered[0] else None
        return ordered[0]

    def choose_action(self, observation: Observation) -> Action:
        from src.ai.tactics import coordinated_wolf, distances, explore_beyond_sight, forage_safely
        self.runner_up = None
        if observation.actor.side == "prey":
            action, self.runner_up = forage_safely(observation)
            return action
        actor, grid = observation.actor, observation.grid
        targets = [a for a in observation.agents if a.alive and a.side == "prey" and not a.escape_guard]
        if not targets:
            return self._search(observation, distances, explore_beyond_sight)
        nearest = min(targets, key=lambda prey: (grid.chebyshev_distance(actor.pos, prey.pos), prey.agent_id))
        self._tracks[actor.agent_id] = nearest.pos
        options = [(tile, target) for tile in observation.legal_destinations for target in targets
                   if grid.chebyshev_distance(tile, target.pos) == 1]
        if actor.can_attack() and options:
            ordered = sorted(options, key=lambda pair: (pair[1].hp,
                             grid.chebyshev_distance(actor.pos, pair[0]), pair[0], pair[1].agent_id))
            tile, target = ordered[0]
            self.runner_up = ordered[1][0] if len(ordered) > 1 else None
            return Action(tile, f"Attack {target.agent_id} from reachable approach", "attack", target.agent_id)
        if actor.pack_id:
            action = coordinated_wolf(observation)
            if action is not None and action.destination != actor.pos:
                return action
        blocked = {a.pos for a in observation.agents if a.alive and a.agent_id != actor.agent_id}
        goals = [tile for target in targets for tile in grid.passable_neighbors(target.pos) if tile not in blocked]
        field = distances(grid, goals, blocked)
        tile = self._take_tile(observation.legal_destinations, lambda p: (
            field.get(p, 10000), -observation.influence.get(p, 0), grid.chebyshev_distance(p, actor.pos), p))
        if field.get(tile, 10000) >= 10000:
            tile = self._take_tile(observation.legal_destinations, lambda p: (
                grid.chebyshev_distance(p, nearest.pos), p))
            return Action(tile, "Hunt: close the distance", "wait")
        return Action(tile, "Hunt: approach a reachable target", "wait")

    def _search(self, observation, distances, explore_beyond_sight) -> Action:
        """Keep hunting after prey leaves sight, instead of waiting on the current tile."""
        actor, grid = observation.actor, observation.grid
        blocked = {a.pos for a in observation.agents if a.alive and a.agent_id != actor.agent_id}
        track = self._tracks.get(actor.agent_id)
        if track == actor.pos:
            self._tracks.pop(actor.agent_id, None)
            track = None
        if track is not None:
            field = distances(grid, [track], blocked)
            tile = self._take_tile(observation.legal_destinations, lambda p: (
                field.get(p, 10000), grid.chebyshev_distance(p, actor.pos), p))
            if tile != actor.pos and field.get(tile, 10000) < 10000:
                return Action(tile, "Hunt: search the last place prey was seen", "wait")
            self._tracks.pop(actor.agent_id, None)
        found = explore_beyond_sight(observation)
        if found.destination != actor.pos:
            return Action(found.destination, "Hunt: search unseen ground", "wait")
        if observation.remembered:
            far = max(observation.remembered, key=lambda tile: (grid.chebyshev_distance(actor.pos, tile), tile))
            field = distances(grid, [far], blocked)
            tile = self._take_tile(observation.legal_destinations, lambda p: (
                field.get(p, 10000), grid.chebyshev_distance(p, actor.pos), p))
            if tile != actor.pos:
                return Action(tile, "Hunt: cross known ground", "wait")
        return Action(actor.pos, "Hunt: no trail to follow", "wait")
