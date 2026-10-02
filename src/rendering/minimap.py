"""A small copy of a clearing, using the same tiles the match will draw."""
from __future__ import annotations

import pygame

from src.core.grid import Grid
from src.core.scenario import apply_start
from src.data.loader import CONFIG_DIR, load_battle, load_map, load_named_scenario, load_tiles, sized_scenario

_CACHE: dict[tuple[str, bool, str], pygame.Surface] = {}
_TILE = 16
_HUNTER = (196, 88, 84)
_HERD = (118, 164, 118)
_JACKAL = (214, 160, 72)
_DUEL_FILES = {"ford": "skirmish", "field": "field", "stone": "stone"}


def board_preview(name: str, large: bool, assets, start: str = "noon") -> pygame.Surface:
    key = (name, large, start)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    scenario_name = sized_scenario(name, large)
    scenario = apply_start(load_named_scenario(scenario_name), start)
    grid = Grid(load_map(CONFIG_DIR / scenario.get("map", "map.json")), load_tiles())
    surface = pygame.Surface((grid.width * _TILE, grid.height * _TILE))
    for row in range(grid.height):
        for col in range(grid.width):
            surface.blit(assets.get_tile(grid.tiles[row][col], _TILE, variant=(row + col) % 4),
                         (col * _TILE, row * _TILE))
    for predator in scenario["predators"]:
        _mark(surface, predator["pos"], _HUNTER)
    for herd in scenario["herds"]:
        _mark(surface, herd["center"], _HERD)
    _CACHE[key] = surface
    return surface


def _mark(surface: pygame.Surface, pos, color) -> None:
    center = (pos[1] * _TILE + _TILE // 2, pos[0] * _TILE + _TILE // 2)
    pygame.draw.circle(surface, (20, 36, 28), center, 6)
    pygame.draw.circle(surface, color, center, 4)


def duel_preview(name: str, large: bool, assets) -> pygame.Surface:
    key = ("duel", name, large)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    stem = _DUEL_FILES[name]
    battle = load_battle(f"{stem}_large" if large else stem)
    grid = Grid(load_map(CONFIG_DIR / battle["map"]), load_tiles())
    surface = pygame.Surface((grid.width * _TILE, grid.height * _TILE))
    for row in range(grid.height):
        for col in range(grid.width):
            surface.blit(assets.get_tile(grid.tiles[row][col], _TILE, variant=(row + col) % 4),
                         (col * _TILE, row * _TILE))
    for fighter in battle["fighters"]:
        _mark(surface, fighter["pos"], _HUNTER if fighter["side"] == "hunter" else _JACKAL)
    _CACHE[key] = surface
    return surface


def _fit(canvas: pygame.Surface, box: pygame.Rect, board: pygame.Surface) -> pygame.Rect:
    scale = min(box.width / board.get_width(), box.height / board.get_height())
    size = (max(1, int(board.get_width() * scale)), max(1, int(board.get_height() * scale)))
    scaled = pygame.transform.scale(board, size)
    dest = scaled.get_rect(center=box.center)
    canvas.blit(scaled, dest)
    return dest


def blit_duel(canvas: pygame.Surface, box: pygame.Rect, name: str, large: bool, assets) -> pygame.Rect:
    return _fit(canvas, box, duel_preview(name, large, assets))


def blit_preview(canvas: pygame.Surface, box: pygame.Rect, name: str, large: bool, assets,
                 start: str = "noon") -> pygame.Rect:
    return _fit(canvas, box, board_preview(name, large, assets, start))
