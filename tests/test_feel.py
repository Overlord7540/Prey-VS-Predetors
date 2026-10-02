"""The camera eases, the goal line leaves, and an action has one cue."""
import math

from src.core.scenario import build_default_scenario
from src.rendering.camera import Camera
from src.rendering.renderer import goal_alpha, goal_sentence
from src.rendering.sounds import cue_for


def test_the_camera_eases_toward_the_actor_then_rests():
    camera = Camera(20, 20)
    camera.glance((19, 19))
    assert camera._target == (320, 560)
    camera.follow(0.05)
    assert 0 < camera.x < 320 and camera._target is not None
    for _ in range(90):
        camera.follow(1 / 60)
    assert camera._target is None
    assert camera.tile_at((959, 719)) == (19, 19)


def test_a_fitted_board_and_a_manual_pan_do_not_keep_gliding():
    fitted = Camera(10, 8, tile_size=32)
    fitted.glance((7, 7))
    assert fitted._target is None
    camera = Camera(20, 20)
    camera.glance((19, 19))
    camera.pan(4, 0)
    assert camera._target is None and camera.x == 4


def test_the_goal_line_names_this_clearing_and_then_leaves():
    sim = build_default_scenario(seed=1, scenario_name="glade")
    rules = sim.grid.rules
    taken = math.ceil(sim.starting_prey_count * rules.predator_win_prey_elimination_pct)
    eaten = math.ceil(sim.starting_resource_total * rules.prey_win_resource_pool_pct)
    assert goal_sentence(sim) == f"Hunters need {taken} taken down. The herd needs {eaten} eaten."
    assert goal_alpha(0) == 255 and goal_alpha(4.0) == 255
    assert goal_alpha(5.0) == 0
    assert goal_sentence(type("Skirmish", (), {"kind": "skirmish"})()) == "Clear the other side."


def test_a_step_a_bite_and_feeding_each_pick_one_cue():
    sim = build_default_scenario(seed=1, scenario_name="glade")
    sim.step_action()
    sim.step_action()
    assert cue_for(sim.events, sim.last_action) == "step"
    bite = type("Event", (), {"kind": "hit"})()
    assert cue_for([bite], sim.last_action) == "bite"
    fed = type("Action", (), {"food_consumed": 1, "before": (0, 0), "after": (0, 1)})()
    assert cue_for([], fed) == "feed"
