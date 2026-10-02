from src.core.control import Action
from src.core.scenario import build_default_scenario
from src.core.agent import PreyState
from tests.support import make_sim


def test_fast_stops_at_human_turn():
    for side in ("predator", "prey"):
        sim = build_default_scenario(seed=42)
        sim.player_side = side
        sim.step()
        assert sim.human_turn and sim.turn == 1
        before = [(a.agent_id, a.pos) for a in sim.predators + sim.prey]
        sim.step()
        sim.step_action()
        assert before == [(a.agent_id, a.pos) for a in sim.predators + sim.prey]
        sim.end_player_turn()
        sim.step()
        assert len(sim.history) == 1
        sim.step()
        assert sim.human_turn and sim.turn == 2


def test_player_command_overrides_fear_and_cannot_act_twice():
    sim = make_sim([(5, 4), (5, 6)])
    sim.player_side = "prey"
    sim.step()
    actor = sim.prey[1]
    actor.state = PreyState.DESPAIR
    destination = (5, 7)
    sim.submit_player_action(actor.agent_id, Action(destination))
    assert actor.pos == destination
    try:
        sim.submit_player_action(actor.agent_id, Action((5, 8)))
        assert False, "Second command accepted"
    except ValueError:
        pass
    assert sim.prey[0].agent_id in sim.pending_player_ids


def test_invalid_player_move_preserves_action():
    sim = make_sim([(5, 4), (5, 5)])
    sim.player_side = "prey"
    sim.step()
    for destination in ((5, 5), (9, 11), (True, 4)):
        try:
            sim.submit_player_action("0", Action(destination))
            assert False, "Illegal move accepted"
        except ValueError:
            pass
    assert "0" in sim.pending_player_ids and sim.prey[0].pos == (5, 4)


def test_end_turn_waits_without_automatic_feeding():
    sim = make_sim([(5, 4)])
    food = next(p for p, stock in sim.grid.resources_remaining.items() if stock)
    sim.prey[0].pos = food
    sim.player_side = "prey"
    sim.step()
    before = sim.grid.resources_remaining[food]
    sim.end_player_turn()
    assert sim.prey[0].pos == food
    assert sim.grid.resources_remaining[food] == before
    assert not sim.human_turn and not sim.pending_player_ids
