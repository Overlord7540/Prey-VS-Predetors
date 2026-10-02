"""The duel offers three grounds. The fighters stay the same two packs."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from src.ai.fov import visible_tiles
from src.core.battle import build_battle
from src.rendering.asset_manager import AssetManager
from src.rendering.menu import DUELS, menu_buttons
from src.rendering.minimap import duel_preview


def _sees(battle, name):
    actor = battle.fighters[next(index for index, fighter in enumerate(battle.fighters) if fighter.name == name)]
    seen = visible_tiles(battle.grid, actor.pos, battle.grid.rules.sight_range)
    others = [fighter.name for fighter in battle.fighters if fighter.side != actor.side and fighter.pos in seen]
    return others


def test_the_field_is_open_and_the_stone_hides_the_other_pack():
    field = build_battle("field")
    stone = build_battle("stone")
    assert field.grid.river_row < 0 and not any("rock" in row for row in field.grid.tiles)
    assert _sees(field, "Sable") == ["Cinder", "Nettle", "Bramble"]
    assert _sees(stone, "Sable") == []
    assert stone.grid.tile_props((5, 5)).blocks_los
    assert [fighter.name for fighter in field.fighters] == [fighter.name for fighter in stone.fighters]
    large = build_battle("stone_large")
    assert (large.grid.width, large.grid.height) == (12, 12)
    assert _sees(large, "Sable") == []


def test_duel_picker_scrolls_three_boards():
    pygame.init()
    pygame.display.set_mode((1, 1))
    buttons = menu_buttons((1280, 800), "duel")
    assert [key for _, key, _ in buttons] == [pygame.K_LEFT, pygame.K_RETURN, pygame.K_RIGHT, pygame.K_ESCAPE]
    assert [name for name, _, _ in DUELS] == ["field", "ford", "stone"]
    board = duel_preview("field", False, AssetManager())
    assert board.get_size() == (12 * 16, 10 * 16)
    pygame.quit()
