"""Second map and the buffalo role. Riverlands stays the default match."""
from src.core.control import Action
from src.core.scenario import build_default_scenario
from src.data.loader import CONFIG_DIR, load_map


def test_riverlands_stays_the_default_and_basin_is_a_different_board():
    river = load_map()
    basin = load_map(CONFIG_DIR / "maps" / "basin.json")
    assert river.river_row != basin.river_row
    assert len(river.chokepoints) == 2
    assert len(basin.chokepoints) == 1

    classic = build_default_scenario(seed=1)
    assert {prey.species for prey in classic.prey} == {"deer"}
    assert classic.grid.river_row == river.river_row

    match = build_default_scenario(seed=1, scenario_name="basin")
    assert match.grid.river_row == basin.river_row
    species = {prey.species for prey in match.prey}
    assert species == {"deer", "buffalo", "giraffe"}
    assert sum(prey.species == "buffalo" for prey in match.prey) == 2
    assert sum(prey.species == "giraffe" for prey in match.prey) == 1
    for prey in match.prey:
        assert match.grid.is_passable(prey.pos)
    for predator in match.predators:
        assert match.grid.is_passable(predator.pos)
        assert predator.pos[0] < match.grid.river_row


def test_buffalo_is_the_slow_high_hp_eater():
    match = build_default_scenario(seed=2, scenario_name="basin")
    buffalo = next(prey for prey in match.prey if prey.species == "buffalo")
    deer = next(prey for prey in match.prey if prey.species == "deer")
    assert buffalo.hp == 60 and deer.hp == 40
    assert max(len(path) - 1 for path in match.movement_paths(buffalo).values()) == 2
    assert max(len(path) - 1 for path in match.movement_paths(deer).values()) == 2
    node = next(pos for pos, stock in match.grid.resources_remaining.items()
                if match.grid.tiles[pos[0]][pos[1]] == "resource_node" and stock == 2)
    buffalo.pos = node
    match._act_prey(buffalo, Action(node, kind="feed"))
    assert match.grid.resources_remaining[node] == 0


def test_water_slows_a_deer_and_a_buffalo_still_crosses():
    match = build_default_scenario(seed=1, scenario_name="basin")
    buffalo = next(prey for prey in match.prey if prey.species == "buffalo")
    deer = next(prey for prey in match.prey if prey.species == "deer")
    river = match.grid.river_row
    for index, prey in enumerate(match.prey):
        if prey not in (buffalo, deer):
            prey.pos = (0, 11 - index)
    buffalo.pos = (river + 1, 0)
    deer.pos = (river + 1, 2)
    assert match.grid.tiles[river][0] == "river"
    assert (river, 0) in match.movement_paths(buffalo)
    assert (river - 1, 0) in match.movement_paths(buffalo)
    assert (river, 2) in match.movement_paths(deer)
    assert (river - 1, 2) not in match.movement_paths(deer)

    match.unit_stats["tiger"].damage_spread = 0
    hunter = match.predators[0]
    hunter.pos = (river + 1, 0)
    buffalo.adrenaline_cooldown = 1
    buffalo.pos = (river + 1, 1)
    match._attack(hunter, buffalo)
    assert buffalo.hp == 60 - 32
    buffalo.hp = 60
    buffalo.alive = True
    buffalo.pos = (river, 0)
    hunter.attack_used = False
    match._attack(hunter, buffalo)
    assert buffalo.hp == 60
    assert match.attack_targets(hunter.agent_id, hunter.pos) == []


def test_a_giraffe_recovers_ten_health_on_its_activation():
    match = build_default_scenario(seed=1, scenario_name="basin")
    giraffe = next(prey for prey in match.prey if prey.species == "giraffe")
    assert giraffe.max_hp == 100
    giraffe.hp = 70
    match._act_prey(giraffe, Action(giraffe.pos, kind="wait"))
    assert giraffe.hp == 80


def test_basin_match_steps_without_changing_the_riverlands_rules():
    match = build_default_scenario(seed=4, scenario_name="basin")
    for _ in range(3):
        match.step()
    assert match.turn == 3
    assert match.winner is None
