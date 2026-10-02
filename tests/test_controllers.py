import random
from dataclasses import replace

from src.core.scenario import build_default_scenario
from src.core.control import Action
from tests.support import FixedController


def run(seed):
    sim = build_default_scenario(seed=seed)
    for _ in range(150):
        if sim.is_over():
            break
        sim.step()
    return sim


def test_seeded_matches_ignore_global_random_and_other_matches():
    original = random.getstate()
    try:
        first = run(41)
        random.seed(998)
        run(2)
        second = run(41)
        assert first.history == second.history
        assert first.winner == second.winner
    finally:
        random.setstate(original)


def test_observation_mutation_cannot_change_live_state():
    sim = build_default_scenario(seed=2)
    actor = sim.prey[0]
    observation = sim.observe(actor.agent_id)
    observation.actor.hp = 0
    observation.actor.pos = (99, 99)
    observation.grid.resources_remaining.clear()
    observation.flock.member_ids.clear()
    assert actor.hp == 40
    assert actor.pos != (99, 99)
    assert sim.grid.resources_remaining
    assert sim.flocks[actor.flock_id].member_ids


def test_injected_illegal_move_is_rejected_by_public_round_step():
    sim = build_default_scenario(seed=5, controllers={"predator": FixedController((999, 999))})
    positions = [p.pos for p in sim.predators]
    sim.step()
    assert [p.pos for p in sim.predators] == positions


def test_controller_observes_legal_choices_and_cannot_teleport_by_editing_snapshot():
    class AdversarialController:
        def choose_action(self, observation):
            observation.actor.pos = (99, 99)
            observation.grid.tiles[0][0] = "open_field"
            return Action((99, 99))
    sim = build_default_scenario(seed=2, controllers={"predator": AdversarialController()})
    positions = [p.pos for p in sim.predators]
    sim.step()
    assert [p.pos for p in sim.predators] == positions


def test_map_threshold_is_used_by_simulation():
    sim = build_default_scenario(seed=2)
    sim.grid.rules = replace(sim.grid.rules, predator_win_prey_elimination_pct=1 / 6)
    sim.prey[0].alive = False
    sim.prey[0].hp = 0
    sim.step()
    assert sim.winner == "predator"


def test_policy_decision_does_not_mutate_observation():
    from copy import deepcopy
    sim = build_default_scenario(seed=2)
    observation = sim.observe(sim.prey[0].agent_id)
    before = deepcopy(observation)
    sim.default_controller.choose_action(observation)
    assert observation.actor == before.actor
    assert observation.flock == before.flock
    assert observation.grid.resources_remaining == before.grid.resources_remaining


def test_custom_detection_range_is_used():
    from tests.support import make_sim
    from src.core.agent import PredatorAgent, PreyState
    sim = make_sim([(0, 5)], PredatorAgent("t", "tiger", (0, 0), "predator"))
    sim.controllers["predator"] = FixedController((0, 0))
    sim.controllers["prey"] = FixedController((0, 5))
    sim.grid.rules = replace(sim.grid.rules, panic_detection_range=2)
    sim.step()
    assert sim.prey[0].state == PreyState.NORMAL
    sim.grid.rules = replace(sim.grid.rules, panic_detection_range=6)
    sim.step()
    assert sim.prey[0].state == PreyState.PANIC


def test_invalid_rules_and_overcrowded_scenario_are_rejected():
    from src.core.rules import Rules
    from src.data.loader import load_scenario
    for kwargs in [{"panic_detection_range": -1}, {"prey_win_resource_pool_pct": 1.1}]:
        try:
            Rules(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid rule accepted")
    config = load_scenario()
    config["herds"][0]["count"] = 999
    try:
        build_default_scenario(seed=1, scenario=config)
    except ValueError:
        pass
    else:
        raise AssertionError("Overcrowded scenario accepted")


def test_batch_records_caps_and_is_repeatable():
    from src.experiments.run import run_batch
    first = run_batch(start_seed=5, matches=2, max_rounds=1)
    assert first == run_batch(start_seed=5, matches=2, max_rounds=1)
    assert first["outcomes"] == {"unfinished": 2}
    assert [m["seed"] for m in first["matches"]] == [5, 6]
    assert "scenario.json" in first["configuration"]
