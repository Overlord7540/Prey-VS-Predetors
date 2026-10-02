"""Tutorial clearings and the later animals."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from src.core.scenario import build_default_scenario
from src.rendering.asset_manager import AssetManager
from src.rendering.menu import CLEARINGS, menu_buttons
from src.rendering.minimap import board_preview


def test_glade_is_open_and_steps_are_short():
    match = build_default_scenario(seed=1, scenario_name="glade")
    assert match.lesson == "glade"
    assert match.grid.river_row == -1
    assert {prey.species for prey in match.prey} == {"deer"}
    deer = match.prey[0]
    assert max(len(path) - 1 for path in match.movement_paths(deer).values()) == 2


def test_rocks_block_the_line_between_wolf_and_deer():
    match = build_default_scenario(seed=1, scenario_name="rocks")
    wolf = match.observe("wolf_1")
    assert match.prey[0].pos not in wolf.visible


def test_rookery_animals_differ_in_sight_panic_and_pack():
    match = build_default_scenario(seed=1, scenario_name="rookery")
    species = {unit.species for unit in match.predators + match.prey}
    assert {"jackal", "hare", "heron", "deer"} <= species
    assert {jackal.pack_id for jackal in match.predators} == {"jackal_pack"}
    heron = next(prey for prey in match.prey if prey.species == "heron")
    hare = next(prey for prey in match.prey if prey.species == "hare")
    deer = next(prey for prey in match.prey if prey.species == "deer")
    assert len(match.observe(heron.agent_id).visible) > len(match.observe(deer.agent_id).visible)
    assert max(len(path) - 1 for path in match.movement_paths(heron).values()) == 1
    assert match.unit_stats["hare"].panic_range > match.grid.rules.panic_detection_range
    assert hare.pos[0] > match.grid.river_row


def test_dawn_and_dusk_move_the_same_animals():
    from src.data.loader import sized_scenario
    names = ["glade", "rocks", "ford", "rookery", "riverlands", "basin"]
    for name in names:
        for large in (False, True):
            scenario_name = sized_scenario(name, large)
            if scenario_name != name and large is False:
                continue
            noon = build_default_scenario(seed=1, scenario_name=scenario_name, start="noon")
            for start in ("dawn", "dusk"):
                other = build_default_scenario(seed=1, scenario_name=scenario_name, start=start)
                assert [(unit.species, unit.agent_id) for unit in noon.predators] == [
                    (unit.species, unit.agent_id) for unit in other.predators]
                assert {unit.pos for unit in noon.predators + noon.prey} != {
                    unit.pos for unit in other.predators + other.prey}
                assert other.start_name == start


def test_a_decision_names_the_mind_and_what_it_saw():
    match = build_default_scenario(seed=1, scenario_name="glade")
    match.step()
    note = match.briefing
    assert note.mind == "Wary"
    assert note.seen and note.step and note.declined
    assert note.actor_id


def test_clearing_picker_scrolls_and_shows_the_board():
    pygame.init()
    pygame.display.set_mode((1, 1))
    buttons = menu_buttons((1280, 800), "clearing")
    assert [key for _, key, _ in buttons] == [
        pygame.K_LEFT, pygame.K_RETURN, pygame.K_RIGHT,
        pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_ESCAPE,
    ]
    canvas = pygame.Rect(0, 0, 1280, 800)
    for rect, _key, _label in buttons:
        assert canvas.contains(rect)
    assets = AssetManager()
    small = board_preview("riverlands", False, assets)
    large = board_preview("riverlands", True, assets)
    assert large.get_width() > small.get_width()
    glade = board_preview("glade", False, assets)
    assert glade.get_size() == (10 * 16, 8 * 16)
    assert len(CLEARINGS) == 6
    pygame.quit()
