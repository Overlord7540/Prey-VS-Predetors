import random

from src.ai.pathfinding import a_star
from src.core.agent import Flock, PredatorAgent, PredatorIntent, PreyAgent, PreyState
from src.core.grid import Grid
from src.core.scenario import build_default_scenario
from src.core.simulation import Simulation
from src.data.loader import load_map, load_tiles, load_units


from tests.support import make_sim


def test_rejects_overlapping_and_impassable_spawns():
    for positions in [[(0, 0), (0, 0)], [(10, 9)]]:
        try:
            make_sim(positions)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid spawn was accepted")


def test_defaults_and_movement_never_overlap():
    state = random.getstate()
    try:
        for seed in range(20):
            sim = build_default_scenario(seed=seed)
            for _ in range(80):
                living = [a for a in sim.predators + sim.prey if a.alive]
                assert len({a.pos for a in living}) == len(living)
                assert all(sim.grid.is_passable(a.pos) for a in living)
                if sim.is_over():
                    break
                sim.step()
    finally:
        random.setstate(state)


def test_pathfinding_routes_around_occupied_cells():
    grid = Grid(load_map(), load_tiles())
    blocked = {(0, 1), (1, 1)}
    path = a_star(grid, (0, 0), (0, 2), blocked=blocked)
    assert path and not set(path) & blocked
    assert a_star(grid, (0, 0), (0, 1), blocked=blocked) is None


def test_adjacent_kill_records_location_and_releases_tile():
    tiger = PredatorAgent("t", "tiger", (0, 0), "predator", intent=PredatorIntent.CHASE)
    sim = make_sim([(0, 1), (9, 11)], tiger)
    sim.prey[0].hp = 10
    sim.step()
    assert tiger.pos == (0, 0)
    assert not sim.prey[0].alive
    event = next(e for e in sim.events if e.kind == "kill")
    assert (event.actor, event.target, event.pos) == ("t", "0", (0, 1))
    assert (0, 1) not in sim.occupied_positions()
    sim._move_agent(tiger, (0, 1))
    assert tiger.pos == (0, 1)


def test_sequential_moves_reserve_destination():
    sim = make_sim([(0, 0), (0, 2)])
    sim._move_agent(sim.prey[0], (0, 1))
    sim._move_agent(sim.prey[1], (0, 1))
    assert [p.pos for p in sim.prey] == [(0, 1), (0, 2)]


def test_fleeing_does_not_enter_predator_tile():
    for state in [PreyState.PANIC, PreyState.DESPAIR]:
        tiger = PredatorAgent("t", "tiger", (0, 1), "predator")
        sim = make_sim([(0, 0), (1, 0)], tiger)
        for prey in sim.prey:
            prey.state = state
        sim._prey_turn()
        positions = [a.pos for a in sim.predators + sim.prey if a.alive]
        assert len(positions) == len(set(positions))


def test_depletion_event_and_retarget_allow_prey_victory():
    sim = make_sim([(0, 1)])
    sim.step()
    assert sim.grid.resources_remaining[(0, 1)] == 0
    assert [(e.kind, e.pos) for e in sim.events] == [("depleted", (0, 1))]
    sim.step()
    assert sim.prey[0].pos != (0, 1)
    assert not any(e.pos == (0, 1) for e in sim.events)
    for _ in range(300):
        if sim.is_over():
            break
        sim.step()
    assert sim.winner == "prey"


def test_partial_resource_consumption_only_emits_when_empty():
    sim = make_sim([(1, 10)])
    sim.step()
    assert sim.grid.resources_remaining[(1, 10)] == 1
    assert not sim.events
    sim.step()
    assert sim.grid.resources_remaining[(1, 10)] == 0
    assert len(sim.events) == 1 and sim.events[0].kind == "depleted"


def test_prey_eats_underfoot_instead_of_following_distant_goal():
    sim = make_sim([(1, 10)])
    sim.flocks["f"].shared_goal = (18, 10)
    sim._prey_turn()
    assert sim.prey[0].pos == (1, 10)
    assert sim.grid.resources_remaining[(1, 10)] == 1


def test_occupied_shared_goal_does_not_stop_local_foraging():
    sim = make_sim([(0, 1), (0, 3)])
    sim.flocks["f"].shared_goal = (0, 1)
    sim.grid.resources_remaining[(0, 3)] = 0
    from src.ai.fsm import step_prey
    mover = sim.prey[1]
    destination = step_prey(sim.grid, mover, sim.flocks["f"], None, sim.prey,
                            occupied=sim.occupied_positions(mover))
    assert destination != mover.pos and destination != (0, 1)
    assert sim.grid.resources_remaining.get(destination, 0) > 0


def test_despair_recovers_when_threat_is_distant():
    tiger = PredatorAgent("t", "tiger", (9, 11), "predator")
    sim = make_sim([(0, 1)], tiger)
    sim.prey[0].state = PreyState.DESPAIR
    sim._prey_turn()
    assert sim.prey[0].state == PreyState.NORMAL
    assert sim.grid.resources_remaining[(0, 1)] == 0


def test_wolf_skips_attack_for_whole_turn_after_kill():
    wolf = PredatorAgent("w", "wolf", (0, 0), "predator", intent=PredatorIntent.CHASE)
    sim = make_sim([(0, 1), (1, 0), (9, 11)], wolf)
    for prey in sim.prey:
        prey.hp = 10
    sim._predator_turn()
    assert sum(not p.alive for p in sim.prey) == 1
    sim._predator_turn()
    assert sum(not p.alive for p in sim.prey) == 1
    sim._predator_turn()
    assert sum(not p.alive for p in sim.prey) == 2
