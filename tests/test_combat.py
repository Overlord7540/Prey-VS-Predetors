from src.core.agent import PredatorAgent, PreyAgent
from src.core.combat import resolve_attack, zone_of_control
from src.core.grid import Grid
from src.data.loader import load_map, load_tiles, load_units


def make_grid():
    return Grid(load_map(), load_tiles())


def test_tiger_one_shots_giraffe():
    units = load_units()
    tiger = PredatorAgent(agent_id="t1", species="tiger", pos=(0, 0), side="predator")
    giraffe = PreyAgent(agent_id="g1", species="giraffe", pos=(0, 1), side="prey",
                         hp=units["giraffe"].hp, max_hp=units["giraffe"].hp, flock_id="f1")
    resolve_attack(tiger, giraffe, units)
    assert giraffe.alive is False


def test_wolf_needs_two_hits_on_giraffe_and_wounds_persist():
    units = load_units()
    wolf = PredatorAgent(agent_id="w1", species="wolf", pos=(0, 0), side="predator")
    giraffe = PreyAgent(agent_id="g1", species="giraffe", pos=(0, 1), side="prey",
                         hp=units["giraffe"].hp, max_hp=units["giraffe"].hp, flock_id="f1")

    resolve_attack(wolf, giraffe, units)
    assert giraffe.alive is True
    assert giraffe.hp == 40  # 100 - 60

    wolf.cooldown_remaining = 0  # simulate cooldown clearing on a later turn
    resolve_attack(wolf, giraffe, units)
    assert giraffe.alive is False


def test_wolf_cooldown_is_per_wolf_not_pack_wide():
    units = load_units()
    wolf_a = PredatorAgent(agent_id="wa", species="wolf", pos=(0, 0), side="predator", pack_id="p1")
    wolf_b = PredatorAgent(agent_id="wb", species="wolf", pos=(0, 1), side="predator", pack_id="p1")
    deer = PreyAgent(agent_id="d1", species="deer", pos=(0, 2), side="prey",
                      hp=units["deer"].hp, max_hp=units["deer"].hp, flock_id="f1")

    resolve_attack(wolf_a, deer, units)
    assert wolf_a.cooldown_remaining == 1
    assert wolf_b.cooldown_remaining == 0  # unaffected packmate


def test_zone_of_control_includes_self_and_adjacent_tiles():
    grid = make_grid()
    tiger = PredatorAgent(agent_id="t1", species="tiger", pos=(5, 5), side="predator")
    zoc = zone_of_control(grid, tiger)
    assert (5, 5) in zoc
    assert len(zoc) >= 5  # self + at least some neighbors (edges/rocks may reduce passable count)
