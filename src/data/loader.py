"""
Loads config/units.json, config/tiles.json, and config/map.json into
plain dataclasses so the rest of the codebase never touches raw JSON.

This is the ONLY module that should call json.load() on the config files.
Everything else imports UnitStats / TileProps / MapLayout from here.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


@dataclass
class UnitStats:
    name: str
    side: str  # "predator" | "prey"
    hp: int | None = None
    damage: int | None = None
    one_shot_kill: bool = False
    grouping: str | None = None  # "solitary" | "pack"
    move_range: int = 1
    water_move_range: int = 1
    resource_yield: int = 0
    cooldown_after_kill: int = 0
    intent_bias: str | None = None  # "chase" | "ambush" | "camp"
    recovery_hp_per_turn: int = 0
    wounds_persist_across_turns: bool = False
    vulnerable_at_water_midtile: bool = False


@dataclass
class TileProps:
    name: str
    passable: bool
    blocks_los: bool
    provides_concealment: bool
    is_water: bool
    is_resource: bool
    resource_value: int = 0


@dataclass
class MapLayout:
    width: int
    height: int
    river_row: int
    chokepoints: List[dict]
    feeding_grounds: List[dict]
    resource_nodes: List[dict]
    rocks: List[dict]
    win_conditions: dict = field(default_factory=dict)


def load_units(path: Path = CONFIG_DIR / "units.json") -> Dict[str, UnitStats]:
    raw = json.loads(path.read_text())
    return {name: UnitStats(name=name, **{k: v for k, v in stats.items() if k != "notes"})
            for name, stats in raw.items()}


def load_tiles(path: Path = CONFIG_DIR / "tiles.json") -> Dict[str, TileProps]:
    raw = json.loads(path.read_text())
    return {name: TileProps(name=name, **props) for name, props in raw.items()}


def load_map(path: Path = CONFIG_DIR / "map.json") -> MapLayout:
    raw = json.loads(path.read_text())
    return MapLayout(**raw)


if __name__ == "__main__":
    # quick manual sanity check: python -m src.data.loader
    units = load_units()
    tiles = load_tiles()
    game_map = load_map()
    print(f"Loaded {len(units)} units, {len(tiles)} tile types, "
          f"{game_map.width}x{game_map.height} map")
