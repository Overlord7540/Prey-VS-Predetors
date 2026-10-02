"""One battle roster on one map. Wildlife scenarios do not load this."""
from __future__ import annotations

from dataclasses import dataclass

from src.core.grid import Grid
from src.data.loader import CONFIG_DIR, load_battle, load_map, load_tiles, load_units

BODIES = ("tiger", "wolf", "deer", "buffalo", "jackal")


@dataclass(frozen=True)
class Fighter:
    name: str
    body: str
    side: str
    pos: tuple[int, int]
    hp: int
    move_range: int
    damage: int
    damage_spread: int


@dataclass(frozen=True)
class Battle:
    name: str
    grid: Grid
    fighters: tuple[Fighter, ...]

    def side(self, side: str) -> tuple[Fighter, ...]:
        return tuple(fighter for fighter in self.fighters if fighter.side == side)


def build_battle(name: str = "skirmish") -> Battle:
    raw = load_battle(name)
    units = load_units()
    grid = Grid(load_map(CONFIG_DIR / raw["map"]), load_tiles())
    fighters = []
    occupied = set()
    for entry in raw["fighters"]:
        fighter = _fighter(entry, units)
        if fighter.name in {known.name for known in fighters}:
            raise ValueError(f"Duplicate fighter: {fighter.name}")
        if not grid.is_passable(fighter.pos) or fighter.pos in occupied:
            raise ValueError(f"{fighter.name} has no free tile at {fighter.pos}")
        occupied.add(fighter.pos)
        fighters.append(fighter)
    hunters = [fighter for fighter in fighters if fighter.side == "hunter"]
    herd = [fighter for fighter in fighters if fighter.side == "herd"]
    if len(hunters) != 3 or len(herd) != 3:
        raise ValueError("A battle is three fighters on each side")
    return Battle(name=name, grid=grid, fighters=tuple(fighters))


def _fighter(entry: dict, units: dict) -> Fighter:
    try:
        name = entry["name"]
        body = entry["body"]
        side = entry["side"]
        pos = tuple(entry["pos"])
        hp = entry["hp"]
        move_range = entry["move_range"]
        damage = entry["damage"]
        spread = entry["damage_spread"]
    except (KeyError, TypeError) as error:
        raise ValueError("Fighter is missing a required field") from error
    if body not in BODIES or body not in units:
        raise ValueError(f"Unknown body: {body}")
    if side not in ("hunter", "herd"):
        raise ValueError(f"Unknown side: {side}")
    if len(pos) != 2 or type(hp) is not int or hp < 1:
        raise ValueError(f"Invalid fighter: {name}")
    if type(move_range) is not int or move_range < 1 or type(damage) is not int or damage < 1:
        raise ValueError(f"Invalid fighter: {name}")
    if type(spread) is not int or spread < 0:
        raise ValueError(f"Invalid fighter: {name}")
    return Fighter(name, body, side, pos, hp, move_range, damage, spread)
