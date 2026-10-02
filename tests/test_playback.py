import copy
import random

from src.core.scenario import build_default_scenario


def test_detailed_and_fast_rounds_match_previous_rules():
    state = random.getstate()
    try:
        for seed in range(10):
            reference = build_default_scenario(seed=seed)
            fast = copy.deepcopy(reference)
            detailed = copy.deepcopy(reference)
            for _ in range(100):
                if reference.is_over():
                    break
                reference.events.clear()
                reference.turn += 1
                reference._predator_turn()
                reference._prey_turn()
                reference._check_win_conditions()
                reference._log_turn()
                fast.step()
                events = []
                detailed.step_action()
                events.extend(detailed.events)
                while detailed.phase != "Round complete":
                    detailed.step_action()
                    events.extend(detailed.events)
                assert fast.history == detailed.history == reference.history
                assert fast.prey == detailed.prey == reference.prey
                assert fast.predators == detailed.predators == reference.predators
                assert fast.events == events == reference.events
                assert fast.winner == detailed.winner == reference.winner
    finally:
        random.setstate(state)


def test_switching_to_fast_finishes_current_round_once():
    sim = build_default_scenario()
    expected = copy.deepcopy(sim)
    expected.step()
    sim.step_action()  # Predator phase announcement.
    sim.step_action()  # First predator.
    assert sim.turn == 1 and not sim.history
    sim.step()
    assert sim.history == expected.history
    assert sim.prey == expected.prey
    assert sim.predators == expected.predators
    sim.step_action()
    assert sim.turn == 2 and sim.phase == "Predator turn"
    assert sim.active_agent_id is None


def test_phase_order_and_dead_prey_are_skipped():
    sim = build_default_scenario()
    sim.prey[0].alive = False
    sim.prey[0].hp = 0
    seen = []
    sim.step_action()
    assert sim.phase == "Predator turn" and sim.active_agent_id is None
    while sim.phase != "Round complete":
        sim.step_action()
        if sim.active_agent_id:
            seen.append((sim.phase, sim.active_agent_id))
    assert [phase for phase, _ in seen[:3]] == ["Predator turn"] * 3
    assert all(phase == "Prey turn" for phase, _ in seen[3:])
    assert sim.prey[0].agent_id not in [agent for _, agent in seen]
    assert len(sim.history) == 1
