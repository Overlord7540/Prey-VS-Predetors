"""Display-free checks for menu hit targets and the pixel-art compositor."""
import os
import random
from copy import deepcopy

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from src.core.scenario import build_default_scenario
from src.rendering.asset_manager import AssetManager, LEGEND_ORDER, LEGEND_TILE_ORDER
from src.rendering.controls import button_enabled, draw_buttons, game_buttons
from src.rendering.menu import draw_menu, menu_buttons
from src.rendering.player import PlayerView
from src.rendering.renderer import Renderer, TILE_SIZE
from src.rendering.viewport import fit_viewport, window_to_canvas


@pytest.fixture(scope="module", autouse=True)
def pygame_display():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.mark.parametrize("size", [(960, 720), (840, 710)])
def test_menu_cards_fit_and_remain_clickable_after_window_resize(size):
    bounds = pygame.Rect((0, 0), size)
    buttons = menu_buttons(size)
    assert [key for _, key, _ in buttons] == [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_ESCAPE]
    for index, (rect, key, _) in enumerate(buttons):
        assert bounds.contains(rect)
        assert all(not rect.colliderect(other) for other, _, _ in buttons[index + 1:])
        for window in ((800, 600), (1920, 1080), (960, 1200)):
            left, top, width, height = fit_viewport(size, window)
            click = (left + rect.centerx * width / size[0],
                     top + rect.centery * height / size[1])
            logical = window_to_canvas(click, size, window)
            hits = [candidate_key for candidate, candidate_key, _ in buttons
                    if candidate.collidepoint(logical)]
            assert hits == [key]


@pytest.mark.parametrize("size", [(960, 720), (840, 710)])
def test_menu_text_stays_inside_canvas_and_hover_preserves_labels(size):
    renderer = Renderer(build_default_scenario(seed=3), AssetManager())
    canvas = pygame.Surface(size)
    draw_menu(canvas, renderer)
    idle_labels = [item[0] for item in renderer.text_items]
    idle_art = pygame.image.tobytes(canvas, "RGB")
    first_card = menu_buttons(size)[0][0]
    draw_menu(canvas, renderer, first_card.center)
    assert [item[0] for item in renderer.text_items] == idle_labels
    assert pygame.image.tobytes(canvas, "RGB") != idle_art
    bounds = pygame.Rect((0, 0), size)
    for text, _, pos, font_size, bold, _, centered in renderer.text_items:
        font = pygame.font.SysFont("georgia" if font_size >= 27 else "tahoma", font_size, bold=bold)
        label = pygame.Rect((0, 0), font.size(text))
        if centered:
            label.center = pos
        else:
            label.topleft = pos
        assert bounds.contains(label), f"Text outside menu canvas: {text}"


@pytest.mark.parametrize("window", [(800, 600), (1920, 1080), (960, 1200)])
@pytest.mark.parametrize("view", ["board", "menu"])
def test_graphics_and_native_text_render_through_resized_viewports(window, view):
    sim = build_default_scenario(seed=7)
    sim.step()
    renderer = Renderer(sim, AssetManager())
    renderer.capture_events()
    renderer.selected_agent_id = next(agent.agent_id for agent in sim.prey if agent.alive)
    canvas = pygame.Surface(renderer.screen_size())
    before_state = deepcopy((sim.predators, sim.prey, sim.flocks, sim.grid.resources_remaining,
                             sim.turn, sim.history, sim.winner, sim.events, sim.decision_reasons))
    random_state = random.getstate()
    simulation_random_state = sim.rng.getstate()
    if view == "menu":
        draw_menu(canvas, renderer, menu_buttons(canvas.get_size())[1][0].center)
    else:
        renderer.draw(canvas)
    assert renderer.text_items
    screen = pygame.Surface(window)
    viewport = pygame.Rect(fit_viewport(canvas.get_size(), window))
    screen.blit(pygame.transform.scale(canvas, viewport.size), viewport)
    before_text = pygame.image.tobytes(screen, "RGB")
    previous_clip = screen.get_clip()
    renderer.draw_text(screen, viewport)
    assert screen.get_clip() == previous_clip
    assert pygame.image.tobytes(screen, "RGB") != before_text
    # Native text must not leak into the letterbox around the logical canvas.
    for point in ((0,0),(window[0]-1,0),(0,window[1]-1),(window[0]-1,window[1]-1)):
        if not viewport.collidepoint(point):
            assert screen.get_at(point) == (0,0,0,255)
    assert before_state == (sim.predators, sim.prey, sim.flocks, sim.grid.resources_remaining,
                            sim.turn, sim.history, sim.winner, sim.events, sim.decision_reasons)
    assert random.getstate() == random_state
    assert sim.rng.getstate() == simulation_random_state


def test_pixel_assets_are_cached_deterministic_and_do_not_change_random_state():
    state = random.getstate()
    assets = AssetManager()
    independent_assets = AssetManager()
    for species in LEGEND_ORDER:
        sprite = assets.get_sprite(species, 32, include_label=False)
        assert sprite is assets.get_sprite(species, 32, include_label=False)
        assert sprite.get_size() == (32, 32)
        assert pygame.image.tobytes(sprite, "RGBA") == pygame.image.tobytes(
            independent_assets.get_sprite(species, 32, include_label=False), "RGBA")
        assert 0 < pygame.mask.from_surface(sprite).count() < 32 * 32
    for tile in LEGEND_TILE_ORDER:
        rendered = assets.get_tile(tile, 32, variant=2)
        assert rendered is assets.get_tile(tile, 32, variant=2)
        assert rendered.get_size() == (32, 32)
        assert pygame.image.tobytes(rendered, "RGB") == pygame.image.tobytes(
            independent_assets.get_tile(tile, 32, variant=2), "RGB")
    for food_tile in ("feeding_ground", "resource_node"):
        full = pygame.image.tobytes(assets.get_tile(food_tile, 32), "RGB")
        depleted = pygame.image.tobytes(assets.get_tile(food_tile, 32, depleted=True), "RGB")
        assert full != depleted
    assert random.getstate() == state


@pytest.mark.parametrize("side", [None, "predator", "prey"])
def test_toolbar_hit_targets_match_rendered_buttons_after_resize(side):
    sim = build_default_scenario(seed=11)
    sim.player_side = side
    renderer = Renderer(sim, AssetManager())
    player = PlayerView(sim)
    size = renderer.screen_size()
    bounds = pygame.Rect((0, 0), size)
    canvas = pygame.Surface(size)
    for detailed, paused in ((True, False), (False, True)):
        buttons = game_buttons(renderer, detailed, paused)
        keys = {key for _, key, _ in buttons}
        assert (pygame.K_e in keys) == bool(side)
        assert pygame.K_w not in keys
        assert (pygame.K_n in keys) == (side is None)
        renderer.text_items.clear()
        draw_buttons(canvas, renderer, player, buttons, buttons[0][0].center)
        assert [item[0] for item in renderer.text_items] == [label for _, _, label in buttons]
        for index, (rect, key, _) in enumerate(buttons):
            assert bounds.contains(rect)
            assert rect.width > 0 and rect.height > 0
            assert all(not rect.colliderect(other) for other, _, _ in buttons[index + 1:])
            for window in ((800, 600), (1920, 1080), (960, 1200)):
                left, top, width, height = fit_viewport(size, window)
                click = (left + rect.centerx * width / size[0],
                         top + rect.centery * height / size[1])
                logical = window_to_canvas(click, size, window)
                hits = [candidate_key for candidate, candidate_key, _ in buttons
                        if candidate.collidepoint(logical)]
                assert hits == [key]


@pytest.mark.parametrize("side", ["predator", "prey"])
def test_toolbar_availability_follows_player_selection_and_turn(side):
    sim = build_default_scenario(seed=11)
    sim.player_side = side
    player = PlayerView(sim)
    assert not button_enabled(pygame.K_e, sim, player)
    assert not button_enabled(pygame.K_w, sim, player)
    sim.step()
    assert sim.human_turn
    assert button_enabled(pygame.K_e, sim, player)
    assert not button_enabled(pygame.K_w, sim, player)
    assert not button_enabled(pygame.K_n, sim, player)
    actor = next(agent for agent in sim.predators + sim.prey
                 if agent.agent_id in sim.pending_player_ids)
    point = (actor.pos[1] * TILE_SIZE + TILE_SIZE // 2,
             actor.pos[0] * TILE_SIZE + TILE_SIZE // 2)
    player.click(point)
    assert player.selected == actor.agent_id
    assert button_enabled(pygame.K_w, sim, player)
    assert player.wait()
    assert actor.agent_id not in sim.pending_player_ids
    assert not button_enabled(pygame.K_w, sim, player)
    assert button_enabled(pygame.K_e, sim, player)
    sim.end_player_turn()
    assert not button_enabled(pygame.K_e, sim, player)
    assert not button_enabled(pygame.K_w, sim, player)
    sim.winner = "prey"
    assert not button_enabled(pygame.K_n, sim, player)
    assert button_enabled(pygame.K_r, sim, player)
    assert button_enabled(pygame.K_m, sim, player)


def test_the_decision_book_sits_beside_the_glade():
    sim = build_default_scenario(seed=1, scenario_name="glade")
    sim.step()
    renderer = Renderer(sim, AssetManager())
    notes = renderer._notes_rect()
    origin_x, origin_y = renderer.camera.origin()
    board = pygame.Rect(
        origin_x, origin_y,
        sim.grid.width * renderer.camera.tile_size,
        sim.grid.height * renderer.camera.tile_size,
    )
    assert notes.x >= renderer.camera.width
    assert not notes.colliderect(board)
    for rect, _key, _label in game_buttons(renderer, True, False):
        assert not notes.colliderect(rect)


def test_a_planned_duel_step_draws_the_fighter():
    from src.rendering.skirmish import SkirmishMatch
    match = SkirmishMatch("rules", 1, "hunter")
    renderer = Renderer(match, AssetManager())
    player = PlayerView(match, renderer)
    start = match.battle.fighter("Sable").pos
    player.selected = "Sable"
    player.destination = next(tile for tile in match.observe("Sable").legal_destinations if tile != start)
    player.draw(pygame.Surface(renderer.screen_size()), renderer)


def test_a_chosen_tile_opens_commands_beside_it():
    sim = build_default_scenario(seed=11)
    sim.player_side = "prey"
    sim.step()
    renderer = Renderer(sim, AssetManager())
    player = PlayerView(sim, renderer)
    actor = next(agent for agent in sim.prey if agent.agent_id in sim.pending_player_ids)
    player.selected = actor.agent_id
    destination = next(tile for tile in sim.observe(actor.agent_id).legal_destinations if tile != actor.pos)
    player.destination = destination
    labels = [label for _rect, _name, label in player._popup_rects()]
    assert "Wait" in labels and "Cancel" in labels
    cancel = next(rect for rect, name, _label in player._popup_rects() if name == "cancel")
    player.click(cancel.center)
    assert player.destination is None and player.selected == actor.agent_id


def test_guide_replaces_underlying_native_text():
    sim = build_default_scenario(seed=42)
    sim.player_side = "prey"
    sim.step()
    renderer = Renderer(sim, AssetManager())
    renderer.selected_agent_id = sim.prey[0].agent_id
    canvas = pygame.Surface(renderer.screen_size())
    renderer.draw(canvas)
    before = [item for item in renderer.text_items if renderer.help_rect().collidepoint(item[2])]
    assert before
    renderer.show_help = True
    renderer.draw_help(canvas)
    assert all(item not in renderer.text_items for item in before)
    assert any("Field guide" in item[0] for item in renderer.text_items)


def test_clicking_off_board_preserves_selected_unit_and_action():
    sim = build_default_scenario(seed=42)
    sim.player_side = "prey"
    sim.step()
    player = PlayerView(sim)
    player.selected = sim.prey[0].agent_id
    pending = set(sim.pending_player_ids)
    message = player.message
    for point in [(sim.grid.width*TILE_SIZE+10, 250), (-1, 25), (40, sim.grid.height*TILE_SIZE+12)]:
        player.click(point)
        assert player.selected == sim.prey[0].agent_id
        assert sim.pending_player_ids == pending
        assert player.message == message


def test_title_menu_explains_hovered_role():
    renderer = Renderer(build_default_scenario(seed=3), AssetManager())
    canvas = pygame.Surface(renderer.screen_size())
    choices = menu_buttons(canvas.get_size())
    draw_menu(canvas, renderer, choices[1][0].center)
    labels = [item[0] for item in renderer.text_items]
    assert "Command the prey." in labels
    assert "Command the predators." not in labels
