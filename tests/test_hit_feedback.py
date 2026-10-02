"""Hits freeze playback and show a damage number. The match rules stay the same."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pytest

pygame = pytest.importorskip("pygame")

from src.core.records import SimulationEvent
from src.core.scenario import build_default_scenario
from src.rendering.asset_manager import AssetManager
from src.rendering.renderer import Renderer


@pytest.fixture(scope="module", autouse=True)
def pygame_display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def test_a_hit_freezes_the_picture_and_prints_the_damage():
    renderer = Renderer(build_default_scenario(seed=1), AssetManager())
    renderer.sim.events.append(SimulationEvent(1, "hit", (2, 3), "tiger_1", "deer_0", 12))
    renderer.capture_events()
    assert renderer.hit_stop == 0.1
    canvas = pygame.Surface(renderer.screen_size())
    renderer.draw(canvas)
    assert any(item[0] == "-12" for item in renderer.text_items)
    renderer.update(0.05)
    assert renderer.effects[0][1] == 0
    renderer.hit_stop = 0
    renderer.update(0.05)
    assert renderer.effects[0][1] == 0.05


def test_a_kill_holds_longer_than_a_hit_and_a_miss_does_not_hold():
    hit = Renderer(build_default_scenario(seed=1), AssetManager())
    hit.sim.events.append(SimulationEvent(1, "hit", (1, 1), "tiger_1", "deer_0", 8))
    hit.capture_events()
    kill = Renderer(build_default_scenario(seed=1), AssetManager())
    kill.sim.events.append(SimulationEvent(1, "kill", (1, 1), "tiger_1", "deer_0", 40))
    kill.capture_events()
    quiet = Renderer(build_default_scenario(seed=1), AssetManager())
    quiet.sim.events.append(SimulationEvent(1, "depleted", (4, 4), "deer_0", "", 0))
    quiet.capture_events()
    assert kill.hit_stop > hit.hit_stop > 0
    assert quiet.hit_stop == 0
    quiet.draw(pygame.Surface(quiet.screen_size()))
    assert all(item[0] != "EMPTY" for item in quiet.text_items)
