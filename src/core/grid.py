"""
Grid: the 2D tile matrix and pure spatial queries. No Pygame, no agents.

Built from a MapLayout (see src/data/loader.py). Every tile is a tile-type
name (e.g. "open_field", "river") that other modules resolve against
TileProps for passability / line-of-sight / concealment / resource rules.
"""
from __future__ import annotations

from typing import Iterator, List, Tuple

from src.data.loader import MapLayout, TileProps
from src.core.rules import Rules

Coord = Tuple[int, int]  # (row, col)


class Grid:
    def __init__(self, layout: MapLayout, tile_defs: dict[str, TileProps]):
        self.rules = Rules(**layout.win_conditions, **layout.behavior_rules)
        self.river_row = layout.river_row
        self.width = layout.width
        self.height = layout.height
        self.tile_defs = tile_defs
        self.tiles: List[List[str]] = self._build_tiles(layout)
        # remaining resource units per tile, keyed by (row, col)
        self.resources_remaining: dict[Coord, int] = self._build_resources(layout)

    # ---- construction -----------------------------------------------
    def _build_tiles(self, layout: MapLayout) -> List[List[str]]:
        tiles = [["open_field"] * layout.width for _ in range(layout.height)]

        if layout.river_row >= 0:
            for c in range(layout.width):
                tiles[layout.river_row][c] = "river"
            for choke in layout.chokepoints:
                for c in range(choke["col_start"], choke["col_end"] + 1):
                    tiles[layout.river_row][c] = "chokepoint"

        for fg in layout.feeding_grounds:
            for r in range(fg["row"] - fg["radius"], fg["row"] + fg["radius"] + 1):
                for c in range(fg["col"] - fg["radius"], fg["col"] + fg["radius"] + 1):
                    if 0 <= r < layout.height and 0 <= c < layout.width:
                        tiles[r][c] = "feeding_ground"

        for node in layout.resource_nodes:
            tiles[node["row"]][node["col"]] = "resource_node"

        for rock in layout.rocks:
            tiles[rock["row"]][rock["col"]] = "rock"

        return tiles

    def _build_resources(self, layout: MapLayout) -> dict[Coord, int]:
        remaining = {}
        for r in range(layout.height):
            for c in range(layout.width):
                props = self.tile_defs[self.tiles[r][c]]
                if props.is_resource:
                    remaining[(r, c)] = props.resource_value
        return remaining

    # ---- queries -------------------------------------------------------
    def in_bounds(self, pos: Coord) -> bool:
        r, c = pos
        return 0 <= r < self.height and 0 <= c < self.width

    def tile_props(self, pos: Coord) -> TileProps:
        r, c = pos
        return self.tile_defs[self.tiles[r][c]]

    def is_passable(self, pos: Coord) -> bool:
        return self.in_bounds(pos) and self.tile_props(pos).passable

    def is_enterable(self, pos: Coord) -> bool:
        """Land, a ford, or deep water. Deep water is slow except for a buffalo."""
        if not self.in_bounds(pos):
            return False
        props = self.tile_props(pos)
        return props.passable or props.is_water

    def neighbors(self, pos: Coord, diagonals: bool = True) -> Iterator[Coord]:
        r, c = pos
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if diagonals:
            deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in deltas:
            n = (r + dr, c + dc)
            if self.in_bounds(n):
                yield n

    def passable_neighbors(self, pos: Coord, diagonals: bool = True) -> List[Coord]:
        return [n for n in self.neighbors(pos, diagonals) if self.is_passable(n)]

    @staticmethod
    def chebyshev_distance(a: Coord, b: Coord) -> int:
        """8-directional grid distance (matches 'adjacent = 8 possible moves')."""
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

    def resource_nodes_with_stock(self) -> List[Coord]:
        return [pos for pos, amount in self.resources_remaining.items() if amount > 0]

    def consume_resource(self, pos: Coord, amount: int = 1) -> int:
        """Returns the amount actually consumed (capped by what's left)."""
        available = self.resources_remaining.get(pos, 0)
        taken = min(available, amount)
        self.resources_remaining[pos] = available - taken
        return taken

    def total_resources_initial_and_remaining(self) -> Tuple[int, int]:
        # NOTE: caller should snapshot the initial total once at match start
        # for the 65% prey-win aggregate check (see simulation.py).
        remaining = sum(self.resources_remaining.values())
        return remaining, remaining
