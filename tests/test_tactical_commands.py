import pytest
from tests.support import make_sim
from src.core.agent import PredatorAgent
from src.core.control import Action
from src.rendering.camera import Camera


def test_movement_budget_and_adrenaline_extend_reachable_paths():
    sim = make_sim([(5, 5)])
    sim.grid.width = 20
    sim.grid.height = 20
    sim.grid.tiles = [['open_field']*20 for _ in range(20)]
    prey = sim.prey[0]
    assert (5, 7) in sim.movement_paths(prey)
    assert (5, 8) not in sim.movement_paths(prey)
    assert (6, 6) in sim.movement_paths(prey)
    assert (7, 7) not in sim.movement_paths(prey)
    prey.adrenaline = True
    assert (5, 9) in sim.movement_paths(prey)
    assert (5, 10) not in sim.movement_paths(prey)
    for species, budget in [('tiger',3),('wolf',2),('buffalo',2),('giraffe',2)]:
        prey.species = species
        prey.adrenaline = False
        assert max(len(path)-1 for path in sim.movement_paths(prey).values()) == budget


def test_paths_cannot_jump_walls_occupants_or_blocked_corners():
    sim = make_sim([(0, 0), (0, 1)])
    sim.grid.tiles[1][0] = 'rock'
    assert set(sim.movement_paths(sim.prey[0])) == {(0, 0)}
    sim._move_agent(sim.prey[0], (1, 1))
    assert sim.prey[0].pos == (0, 0)


def test_feed_is_explicit_and_wait_does_not_consume_food():
    sim = make_sim([(0, 1)])
    sim.player_side = 'prey'
    sim.step()
    with pytest.raises(ValueError):
        sim.submit_player_action('0', Action((0, 0),kind='feed'))
    assert '0' in sim.pending_player_ids
    sim.submit_player_action('0', Action((0, 1),kind='feed'))
    assert sim.grid.resources_remaining[(0, 1)] == 0


def test_waiting_predator_never_attacks_automatically():
    tiger = PredatorAgent('t','tiger',(0,0),'predator')
    sim = make_sim([(0,1)],tiger)
    sim.player_side = 'predator'
    sim.step()
    sim.end_player_turn()
    assert sim.prey[0].hp == 40 and not tiger.attack_used


def test_camera_zoom_pan_bounds_and_mouse_mapping():
    camera = Camera(20, 20)
    assert camera.tile_at((2 * 64 + 8, 2 * 64 + 8)) == (2, 2)
    assert camera.tile_at((960,50)) is None
    camera.zoom()
    assert camera.tile_size == 32
    for row in range(20):
        for col in range(20):
            point = (col * 32 + 16 + camera.origin()[0], row * 32 + 16 + camera.origin()[1])
            assert camera.tile_at(point) == (row, col)
    camera.zoom()
    assert camera.tile_size == 96
    camera.pan(9999,9999)
    assert camera.tile_at((959,719)) == (19,19)
    camera.pan(-9999,-9999)
    assert camera.tile_at((0,0)) == (0,0)
    camera.focus((19,19))
    assert camera.tile_at((959,719)) == (19,19)


def test_staged_ui_attack_preview_cancel_and_confirmation():
    pygame = pytest.importorskip('pygame')
    from src.rendering.renderer import Renderer
    from src.rendering.asset_manager import AssetManager
    from src.rendering.player import PlayerView
    sim = make_sim([(0,3)],PredatorAgent('t','tiger',(0,0),'predator'))
    sim.player_side = 'predator'
    sim.step()
    view = PlayerView(sim,Renderer(sim,AssetManager()))
    ox, oy = view.renderer.camera.origin()
    tile = view.renderer.camera.tile_size
    view.click((ox + tile // 2, oy + tile // 2))
    view.click((ox + 2 * tile + tile // 2, oy + tile // 2))
    assert sim.predators[0].pos == (0, 0)
    view.attack()
    view.click((ox + 3 * tile + tile // 2, oy + tile // 2))
    assert 'Damage 22-39' in view.preview()
    assert sim.prey[0].hp == 40
    view.reset()
    assert sim.predators[0].pos == (0,0) and 't' in sim.pending_player_ids
    view.click((ox + tile // 2, oy + tile // 2))
    view.click((ox + 2 * tile + tile // 2, oy + tile // 2))
    view.attack()
    view.click((ox + 3 * tile + tile // 2, oy + tile // 2))
    assert view.attack()
    assert sim.predators[0].pos == (0,2) and sim.prey[0].hp < 40
