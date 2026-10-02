"""Default scenario construction, usable without a display or Pygame."""
import copy
import random

from src.ai.fsm import roll_intent
from src.core.agent import Flock, PredatorAgent, PreyAgent
from src.core.grid import Grid
from src.core.simulation import Simulation
from src.data.loader import CONFIG_DIR, load_map, load_tiles, load_units, load_named_scenario


def apply_start(scenario: dict, start: str = "noon") -> dict:
    """Noon keeps the written positions. Dawn and Dusk move the same animals."""
    if start in (None, "", "noon"):
        return scenario
    chosen = scenario.get("starts", {}).get(start)
    if not chosen:
        raise ValueError(f"This clearing has no {start} start")
    scenario = copy.deepcopy(scenario)
    for predator in scenario["predators"]:
        if predator["agent_id"] in chosen:
            predator["pos"] = chosen[predator["agent_id"]]
    for herd in scenario["herds"]:
        if herd["flock_id"] in chosen:
            herd["center"] = chosen[herd["flock_id"]]
    return scenario


def build_default_scenario(seed: int | None = None, controllers=None, scenario=None,
                           scenario_name: str = "riverlands", start: str = "noon") -> Simulation:
    rng = random.Random(seed)
    units = load_units()
    tiles = load_tiles()
    scenario = load_named_scenario(scenario_name) if scenario is None else scenario
    scenario = apply_start(scenario, start)
    game_map = load_map(CONFIG_DIR / scenario.get("map", "map.json"))
    grid = Grid(game_map, tiles)
    predators = []
    for definition in scenario["predators"]:
        species = definition["species"]
        if species not in units or units[species].side != "predator":
            raise ValueError(f"Invalid predator species: {species}")
        predators.append(PredatorAgent(
            agent_id=definition["agent_id"], species=species,
            pos=tuple(definition["pos"]), side="predator"))
    for p in predators:
        p.intent = roll_intent(p.species, rng, units[p.species].intent_bias)
    packs: dict[str, list] = {}
    for predator in predators:
        if units[predator.species].grouping == "pack":
            packs.setdefault(predator.species, []).append(predator)
    for species, members in packs.items():
        if len(members) >= 2:
            for member in members:
                member.pack_id = f"{species}_pack"

    # Separate herds can forage concurrently instead of queueing at one tile.
    occupied = {pred.pos for pred in predators}
    prey = []
    flocks = {}
    for herd in scenario["herds"]:
        species = herd["species"]
        if species not in units or units[species].side != "prey":
            raise ValueError(f"Invalid prey species: {species}")
        count, radius = herd["count"], herd["radius"]
        if type(count) is not int or count < 1 or type(radius) is not int or radius < 0:
            raise ValueError("Herd count must be positive and radius nonnegative")
        row, col = herd["center"]
        flock = Flock(flock_id=herd["flock_id"])
        if flock.flock_id in flocks:
            raise ValueError("Herd IDs must be unique")
        flocks[flock.flock_id] = flock
        spawn_tiles = [(r, c) for r in range(row - radius, row + radius + 1)
                       for c in range(col - radius, col + radius + 1)
                       if grid.is_passable((r, c)) and (r, c) not in occupied]
        if len(spawn_tiles) < count:
            raise ValueError(f"Not enough free tiles for herd {flock.flock_id}")
        for pos in rng.sample(spawn_tiles, count):
            agent_id = f"{species}_{len(prey)}"
            flock.member_ids.append(agent_id)
            occupied.add(pos)
            prey.append(PreyAgent(
                agent_id=agent_id, species=species, side="prey", pos=pos,
                hp=units[species].hp, max_hp=units[species].hp, flock_id=flock.flock_id,
            ))

    match = Simulation(
        grid=grid, unit_stats=units, predators=predators, prey=prey,
        flocks=flocks, seed=seed, rng=rng, controllers=controllers or {},
    )
    match.lesson = scenario.get("lesson", "")
    match.start_name = start or "noon"
    return match

