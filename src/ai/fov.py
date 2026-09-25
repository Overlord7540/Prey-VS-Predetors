"""
Line-of-sight. Two modes, toggled via config (full_awareness is the v1 default):

- full_awareness: predators always know every prey position. No computation.
- los_limited: tile-based sightline check. Rocks block LoS outright; tall
  grass (feeding_ground tiles) grants prey concealment past a short range.

NOTE: v1 ships with full_awareness=True by default (see config/map.json
win_conditions block for other tunables). This module exists so flipping
the toggle doesn't require touching simulation.py.
"""
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


def can_see(grid: Grid, observer: Coord, target: Coord, full_awareness: bool = True) -> bool:
    if full_awareness:
        return True

    if grid.tile_props(target).provides_concealment:
        if Grid.chebyshev_distance(observer, target) > CONCEALMENT_RANGE:
            return False

    for tile in bresenham_line(observer, target)[1:-1]:
        if grid.tile_props(tile).blocks_los:
            return False
    return True
