from copy import deepcopy
from src.ai.policies import TacticalController
from src.ai.tactics import coordinated_wolf
from src.core.agent import PredatorAgent
from src.core.movement import reachable_paths
from tests.support import make_sim


def open_sim(positions, predators=()):
    sim = make_sim(positions)
    sim.predators = list(predators)
    sim.grid.tiles = [["open_field"]*sim.grid.width for _ in range(sim.grid.height)]
    sim.grid.resources_remaining = {}
    return sim


def test_prey_avoids_all_ready_predators_to_reach_food():
    wolves = [PredatorAgent("w1", "wolf", (5, 3), "predator"),
              PredatorAgent("w2", "wolf", (3, 5), "predator")]
    sim = open_sim([(5, 5)], wolves)
    sim.grid.resources_remaining = {(4, 4): 2, (7, 7): 2}
    obs = sim.observe("0")
    before = deepcopy(obs)
    action = TacticalController().choose_action(obs)
    assert action.destination in obs.legal_destinations
    for wolf in wolves:
        reach = reachable_paths(sim.grid, wolf, sim.predators + sim.prey, sim.unit_stats["wolf"])
        assert all(sim.grid.chebyshev_distance(action.destination, tile) > 1 for tile in reach)
    assert obs.agents == before.agents and obs.grid.resources_remaining == before.grid.resources_remaining
    assert action.reason


def test_safe_food_underfoot_is_eaten_before_moving():
    sim = open_sim([(5, 5)])
    sim.grid.resources_remaining = {(5, 5): 2, (6, 6): 2}
    assert TacticalController().choose_action(sim.observe("0")).destination == (5, 5)


def test_wolves_assign_distinct_reachable_approaches():
    wolves = [PredatorAgent("w1", "wolf", (5, 3), "predator"),
              PredatorAgent("w2", "wolf", (3, 5), "predator")]
    sim = open_sim([(5, 5)], wolves)
    first = coordinated_wolf(sim.observe("w1"))
    second = coordinated_wolf(sim.observe("w2"))
    assert first.destination != second.destination
    assert sim.grid.chebyshev_distance(first.destination, (5, 5)) == 1
    assert sim.grid.chebyshev_distance(second.destination, (5, 5)) == 1
    assert "Team hunt 0" in first.reason and "Team hunt 0" in second.reason
    assert coordinated_wolf(sim.observe("w1")) == first
    wolves[0].pos = first.destination
    assert coordinated_wolf(sim.observe("w2")).destination != first.destination


def test_blocked_food_is_not_a_foraging_goal():
    sim = open_sim([(5, 5)])
    sim.grid.resources_remaining = {(3, 3): 2, (7, 7): 2}
    for tile in sim.grid.passable_neighbors((3, 3)):
        sim.grid.tiles[tile[0]][tile[1]] = "rock"
    assert TacticalController().choose_action(sim.observe("0")).destination == (6, 6)


def test_predator_searches_when_prey_is_outside_sight():
    wolf = PredatorAgent("w", "wolf", (9, 11), "predator", pack_id="pack")
    sim = open_sim([(0, 0)], [wolf])
    observation = sim.observe("w")
    assert all(agent.agent_id != "0" for agent in observation.agents)
    action = TacticalController().choose_action(observation)
    assert action.destination != (9, 11)
    assert action.destination in observation.legal_destinations


def test_predator_follows_the_last_place_prey_was_seen():
    tiger = PredatorAgent("t", "tiger", (0, 0), "predator")
    sim = open_sim([(0, 2)], [tiger])
    controller = TacticalController()
    controller.choose_action(sim.observe("t"))
    sim.prey[0].pos = (9, 11)
    action = controller.choose_action(sim.observe("t"))
    assert action.destination != (0, 0)
    assert sim.grid.chebyshev_distance(action.destination, (0, 2)) < sim.grid.chebyshev_distance((0, 0), (0, 2))
    assert "last place" in action.reason


def test_a_calm_hunter_spends_its_whole_move_closing_in():
    from src.ai.policies import RuleBasedController
    tiger = PredatorAgent("t", "tiger", (5, 1), "predator")
    sim = open_sim([(5, 6)], [tiger])
    observation = sim.observe("t")
    action = RuleBasedController().choose_action(observation)
    assert action.destination in observation.legal_destinations
    assert sim.grid.chebyshev_distance((5, 1), action.destination) > 1
    assert sim.grid.chebyshev_distance(action.destination, (5, 6)) < sim.grid.chebyshev_distance((5, 1), (5, 6))


def test_wary_prey_steps_away_from_a_hunter_already_beside_it():
    wolf = PredatorAgent("w", "wolf", (5, 6), "predator")
    sim = open_sim([(5, 5)], [wolf])
    sim.grid.resources_remaining = {(8, 8): 2}
    action = TacticalController().choose_action(sim.observe("0"))
    assert sim.grid.chebyshev_distance(action.destination, wolf.pos) > 1


def test_a_scored_mind_takes_a_bite_instead_of_walking_past_it():
    from src.ai.sense import sensible_destination
    tiger = PredatorAgent("t", "tiger", (5, 5), "predator")
    sim = open_sim([(5, 6)], [tiger])
    observation = sim.observe("t")
    taken = sensible_destination(observation, (5, 3))
    assert sim.grid.chebyshev_distance(taken, (5, 6)) == 1
    prey_view = sim.observe("0")
    left = sensible_destination(prey_view, prey_view.actor.pos)
    assert sim.grid.chebyshev_distance(left, tiger.pos) > 1


def test_decision_reason_is_recorded_for_ui():
    sim = open_sim([(5, 5)])
    sim.step_action()
    sim.step_action()
    sim.step_action()
    assert sim.decision_reasons["0"]
