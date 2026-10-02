"""Tile sight. Rocks block the line. Tall grass hides a tile past a short range."""
from __future__ import annotations

from typing import Tuple

from src.core.grid import Grid

Coord = Tuple[int, int]

CONCEALMENT_RANGE = 3  # tiles beyond which tall grass fully hides a unit


def bresenham_line(a: Coord, b: Coord) -> list[Coord]:
    """Simple tile-based line for sightline checks."""
    r0, c0 = a
    r1, c1 = b
    points = []
    dr, dc = abs(r1 - r0), abs(c1 - c0)
    sr = 1 if r0 < r1 else -1
    sc = 1 if c0 < c1 else -1
    err = dr - dc
    r, c = r0, c0
    while True:
        points.append((r, c))
        if (r, c) == (r1, c1):
            break
        e2 = 2 * err
        if e2 > -dc:
            err -= dc
            r += sr
        if e2 < dr:
            err += dr
            c += sc
    return points


def can_see(grid: Grid, observer: Coord, target: Coord, full_awareness: bool = False) -> bool:
    if not grid.in_bounds(target):
        return False
    if full_awareness:
        return True
    if grid.tile_props(target).provides_concealment:
        if Grid.chebyshev_distance(observer, target) > CONCEALMENT_RANGE:
            return False
    for tile in bresenham_line(observer, target)[1:-1]:
        if grid.in_bounds(tile) and grid.tile_props(tile).blocks_los:
            return False
    return True


def visible_tiles(grid: Grid, origin: Coord, sight_range: int) -> set[Coord]:
    seen = {origin}
    row, col = origin
    for r in range(row - sight_range, row + sight_range + 1):
        for c in range(col - sight_range, col + sight_range + 1):
            tile = (r, c)
            if Grid.chebyshev_distance(origin, tile) <= sight_range and can_see(grid, origin, tile):
                seen.add(tile)
    return seen
