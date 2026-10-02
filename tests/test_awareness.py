"""Slice 3: controllers see a limited copy; the live match stays complete."""
from src.core.agent import PredatorAgent
from tests.support import make_sim


def test_rock_hides_animals_and_food_from_the_observation_only():
    predator = PredatorAgent("t", "tiger", (5, 8), "predator")
    sim = make_sim([(5, 5)], predator)
    sim.grid.tiles[5][6] = "rock"
    sim.grid.resources_remaining[(5, 8)] = 2
    observation = sim.observe("0")
    assert "t" not in [agent.agent_id for agent in observation.agents]
    assert (5, 8) not in observation.visible
    assert (5, 8) not in observation.grid.resources_remaining
    assert sim.grid.resources_remaining[(5, 8)] == 2
    assert any(agent.agent_id == "t" for agent in sim.predators)


def test_visible_enemy_raises_nearby_influence():
    predator = PredatorAgent("t", "tiger", (5, 6), "predator")
    sim = make_sim([(5, 5)], predator)
    sim.grid.tiles = [["open_field"] * sim.grid.width for _ in range(sim.grid.height)]
    observation = sim.observe("0")
    assert any(agent.agent_id == "t" for agent in observation.agents)
    assert observation.influence[(5, 6)] > observation.influence.get((5, 1), 0)


def test_tactical_prey_prefers_the_lower_influence_food():
    from src.ai.policies import TacticalController
    predator = PredatorAgent("t", "tiger", (5, 8), "predator")
    sim = make_sim([(5, 5)], predator)
    sim.grid.tiles = [["open_field"] * sim.grid.width for _ in range(sim.grid.height)]
    sim.grid.resources_remaining = {(5, 3): 2, (5, 7): 2}
    destination = TacticalController().choose_action(sim.observe("0")).destination
    assert sim.grid.chebyshev_distance(destination, (5, 8)) > sim.grid.chebyshev_distance(destination, (5, 3))
