from tests.support import make_sim, fixed_move
from src.core.agent import PredatorAgent, PreyState
from src.core.perception import prepare_prey


def predator(pos):
    return PredatorAgent("t", "tiger", pos, "predator")


def test_detection_range_inclusive_and_nearest_member_selected():
    sim = make_sim([(0, 7), (0, 6), (0, 5)], predator((0, 0)))
    sim._tick_flocks()
    assert [p.state for p in sim.prey] == [PreyState.NORMAL, PreyState.NORMAL, PreyState.PANIC]
    outside = make_sim([(0, 7)], predator((0, 0)))
    outside._tick_flocks()
    assert outside.prey[0].state == PreyState.NORMAL
    boundary = make_sim([(0, 6)], predator((0, 0)))
    boundary._tick_flocks()
    assert boundary.prey[0].state == PreyState.PANIC


def test_equal_threat_distance_prefers_closer_resource():
    sim = make_sim([(6, 0), (0, 6)], predator((0, 0)))
    sim._tick_flocks()
    assert sim.prey[1].state == PreyState.PANIC
    assert sim.prey[0].state == PreyState.NORMAL


def test_lock_blocks_next_n_phases_and_despair_has_priority():
    sim = make_sim([(0, 5), (0, 6)], predator((0, 0)))
    sim._tick_flocks()
    assert sim.flocks["f"].panic_lock_turns == 2
    for _ in range(2):
        sim._tick_flocks()
        assert sim.prey[1].state == PreyState.NORMAL
    sim._tick_flocks()
    assert sim.prey[1].state == PreyState.PANIC
    sim._trigger_despair(sim.prey[0])
    sim.flocks["f"].panic_lock_turns = 0
    sim._tick_flocks()
    assert all(p.state == PreyState.DESPAIR for p in sim.prey)


def test_panic_recovery_uses_six_tiles_despair_uses_three():
    sim = make_sim([(0, 6)], predator((0, 0)))
    p = sim.prey[0]
    p.state = PreyState.PANIC
    prepare_prey(sim.grid, p, sim.flocks["f"], sim.predators)
    assert p.state == PreyState.PANIC
    p.pos = (0, 7)
    prepare_prey(sim.grid, p, sim.flocks["f"], sim.predators)
    assert p.state == PreyState.NORMAL
    p.pos = (0, 4)
    p.state = PreyState.DESPAIR
    prepare_prey(sim.grid, p, sim.flocks["f"], sim.predators)
    assert p.state == PreyState.NORMAL
    p.state = PreyState.PANIC
    prepare_prey(sim.grid, p, sim.flocks["f"], [])
    assert p.state == PreyState.NORMAL


def test_dead_predators_do_not_trigger_panic():
    sim = make_sim([(0, 5)], predator((0, 0)))
    sim.predators[0].alive = False
    sim._tick_flocks()
    assert sim.prey[0].state == PreyState.NORMAL
