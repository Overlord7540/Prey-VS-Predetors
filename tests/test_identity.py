from src.core.scenario import build_default_scenario
from src.rendering.identity import build_labels, describe_agent


def test_individual_labels_are_unique_and_include_dead_animals():
    sim = build_default_scenario()
    agents = sim.predators + sim.prey
    labels = build_labels(agents)
    assert len(set(labels.values())) == len(agents)
    assert labels["deer_0"] == "D1"
    assert labels["wolf_1"] == "W1"
    assert labels["wolf_2"] == "W2"
    sim.prey[0].alive = False
    assert build_labels(agents) == labels


def test_inspection_shows_actual_health_and_effective_intent():
    sim = build_default_scenario()
    prey = sim.prey[0]
    prey.hp = 12
    assert "HP: 12/40" in describe_agent(prey, "D1")
    predator = sim.predators[0]
    predator.is_constant_chase = True
    predator.cooldown_remaining = 1
    lines = describe_agent(predator, "T1")
    assert "Intent: Chase" in lines
    assert "Attack cooldown: 1" in lines
