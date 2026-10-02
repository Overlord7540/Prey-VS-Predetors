"""Exercise the real event loop through settings, side selection and play."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pytest
pygame = pytest.importorskip('pygame')


def test_settings_keyboard_navigation_and_starting_a_match(monkeypatch):
    import src.main as entry
    created = []
    original = entry.Renderer
    def renderer(*args):
        result = original(*args)
        created.append(result)
        return result
    monkeypatch.setattr(entry, 'Renderer', renderer)
    monkeypatch.setattr('sys.argv', ['game', '--seed', '42'])
    class Clock:
        def tick(self, *_):
            return 1000
    monkeypatch.setattr(pygame.time, 'Clock', Clock)
    keys = iter([pygame.K_RETURN, pygame.K_3, pygame.K_z, pygame.K_t,
                 pygame.K_ESCAPE, pygame.K_1, pygame.K_1, pygame.K_4, pygame.K_2, pygame.K_2, pygame.K_e,
                 pygame.K_m, pygame.K_1, pygame.K_1, pygame.K_4, pygame.K_2, pygame.K_3, None])
    def events():
        key = next(keys)
        return [pygame.event.Event(pygame.QUIT)] if key is None else [pygame.event.Event(pygame.KEYDOWN, key=key)]
    monkeypatch.setattr(pygame.event, 'get', events)
    monkeypatch.setattr(pygame.mouse, 'get_pos', lambda: (-100,-100))
    entry.main()
    assert len(created) == 3
    assert created[1].sim.player_side == 'prey'
    assert type(created[1].sim.controllers['predator']).__name__ == 'TacticalController'
    assert created[2].sim.player_side is None
    assert all(r.camera.tile_size == 32 and not r.show_grid for r in created)
    assert all(not r.detailed for r in created)
    assert created[1].sim.turn >= 1


def test_skirmish_menu_starts_a_watchable_battle(monkeypatch):
    import src.main as entry
    created = []
    original = entry.Renderer
    def renderer(*args):
        result = original(*args)
        created.append(result)
        return result
    monkeypatch.setattr(entry, 'Renderer', renderer)
    monkeypatch.setattr('sys.argv', ['game', '--seed', '1'])
    class Clock:
        def tick(self, *_):
            return 1000
    monkeypatch.setattr(pygame.time, 'Clock', Clock)
    keys = iter([pygame.K_RETURN, pygame.K_1, pygame.K_2, pygame.K_RETURN, pygame.K_1, None])
    def events():
        key = next(keys)
        return [pygame.event.Event(pygame.QUIT)] if key is None else [pygame.event.Event(pygame.KEYDOWN, key=key)]
    monkeypatch.setattr(pygame.event, 'get', events)
    monkeypatch.setattr(pygame.mouse, 'get_pos', lambda: (-100, -100))
    entry.main()
    battle = created[-1].sim
    assert battle.kind == 'skirmish'
    assert battle.controller_name == 'rules'
    assert (battle.grid.width, battle.grid.height) == (12, 12)
    assert battle.battle.fighter('Sable').pos[0] > 1
    assert created[-1].labels['Sable'] == 'Sable'


def test_large_board_is_optional():
    from src.core.scenario import build_default_scenario
    from src.data.loader import sized_scenario
    from src.rendering.skirmish import SkirmishMatch
    small = build_default_scenario(seed=1, scenario_name=sized_scenario('riverlands', False))
    large = build_default_scenario(seed=1, scenario_name=sized_scenario('riverlands', True))
    basin = build_default_scenario(seed=1, scenario_name=sized_scenario('basin', True))
    assert (small.grid.width, small.grid.height) == (12, 10)
    assert (large.grid.width, large.grid.height) == (20, 20)
    assert (basin.grid.width, basin.grid.height) == (20, 20)
    fight = SkirmishMatch('rules', 1, battle_name='skirmish_large')
    assert (fight.grid.width, fight.grid.height) == (12, 12)
    assert fight.battle.fighter('Cinder').pos[0] == 10


def test_large_board_is_the_default_and_b_selects_small(monkeypatch):
    import src.main as entry
    created = []
    original = entry.Renderer
    def renderer(*args):
        result = original(*args)
        created.append(result)
        return result
    monkeypatch.setattr(entry, 'Renderer', renderer)
    monkeypatch.setattr('sys.argv', ['game', '--seed', '1'])
    class Clock:
        def tick(self, *_):
            return 1000
    monkeypatch.setattr(pygame.time, 'Clock', Clock)
    keys = iter([pygame.K_RETURN, pygame.K_3, pygame.K_b, pygame.K_ESCAPE,
                 pygame.K_1, pygame.K_2, pygame.K_RETURN, pygame.K_1, pygame.K_m,
                 pygame.K_1, pygame.K_1, pygame.K_4, pygame.K_1, pygame.K_3, None])
    def events():
        key = next(keys)
        return [pygame.event.Event(pygame.QUIT)] if key is None else [pygame.event.Event(pygame.KEYDOWN, key=key)]
    monkeypatch.setattr(pygame.event, 'get', events)
    monkeypatch.setattr(pygame.mouse, 'get_pos', lambda: (-100, -100))
    entry.main()
    assert (created[0].sim.grid.width, created[0].sim.grid.height) == (20, 20)
    assert created[1].large_board is False
    assert (created[1].sim.grid.width, created[1].sim.grid.height) == (12, 10)
    assert (created[2].sim.grid.width, created[2].sim.grid.height) == (12, 10)


def test_back_ends_the_match_and_returns_one_page(monkeypatch):
    import src.main as entry
    created = []
    original = entry.Renderer
    def renderer(*args):
        result = original(*args)
        created.append(result)
        return result
    monkeypatch.setattr(entry, 'Renderer', renderer)
    monkeypatch.setattr('sys.argv', ['game', '--seed', '1'])
    class Clock:
        def tick(self, *_):
            return 1000
    monkeypatch.setattr(pygame.time, 'Clock', Clock)
    keys = iter([pygame.K_RETURN, pygame.K_1, pygame.K_1, pygame.K_1, pygame.K_1, pygame.K_1,
                 pygame.K_ESCAPE, None])
    def events():
        key = next(keys)
        return [pygame.event.Event(pygame.QUIT)] if key is None else [pygame.event.Event(pygame.KEYDOWN, key=key)]
    monkeypatch.setattr(pygame.event, 'get', events)
    monkeypatch.setattr(pygame.mouse, 'get_pos', lambda: (-100, -100))
    entry.main()
    assert created[-1].menu_page == 'sides'


@pytest.mark.parametrize('page', ['title', 'home', 'play', 'clearing', 'duel', 'settings', 'sides', 'face', 'skirmish', 'battle_face', 'classical', 'training'])
def test_menu_focus_and_buttons_fit(page):
    from src.rendering.menu import menu_buttons, draw_menu
    from src.rendering.renderer import Renderer
    from src.rendering.asset_manager import AssetManager
    from src.core.scenario import build_default_scenario
    pygame.init()
    pygame.display.set_mode((1,1))
    renderer = Renderer(build_default_scenario(seed=42), AssetManager())
    renderer.menu_page = page
    canvas = pygame.Surface(renderer.screen_size())
    for i, (rect, key, label) in enumerate(menu_buttons(canvas.get_size(),page)):
        assert canvas.get_rect().contains(rect)
        renderer.menu_focus = i
        draw_menu(canvas,renderer)
        renderer.draw_text(canvas,canvas.get_rect())
    pygame.quit()
