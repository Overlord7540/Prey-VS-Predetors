from src.core.agent import Flock, PredatorAgent, PreyAgent
from src.core.grid import Grid
from src.core.simulation import Simulation
from src.data.loader import load_map, load_tiles, load_units


def make_sim(n_prey=4):
    units = load_units()
    grid = Grid(load_map(), load_tiles())
    predators = [PredatorAgent(agent_id="tiger_1", species="tiger", pos=(0, 0), side="predator")]
    flock = Flock(flock_id="herd", member_ids=[f"deer_{i}" for i in range(n_prey)])
    prey = [
        PreyAgent(agent_id=f"deer_{i}", species="deer", pos=(0, i + 1), side="prey",
                  hp=units["deer"].hp, max_hp=units["deer"].hp, flock_id=flock.flock_id)
        for i in range(n_prey)
    ]
    return Simulation(grid=grid, unit_stats=units, predators=predators, prey=prey,
                       flocks={flock.flock_id: flock})


def test_predator_wins_at_70_percent_elimination():
    sim = make_sim(n_prey=4)
    # kill 3 of 4 (75% >= 70% threshold)
    for p in sim.prey[:3]:
        p.hp = 0
        p.alive = False
    sim._check_win_conditions()
    assert sim.winner == "predator"


def test_no_winner_below_threshold():
    sim = make_sim(n_prey=4)
    sim.prey[0].hp = 0
    sim.prey[0].alive = False  # only 25% eliminated
    sim._check_win_conditions()
    assert sim.winner is None


def test_starting_counts_snapshot_correctly():
    sim = make_sim(n_prey=5)
    assert sim.starting_prey_count == 5
    assert sim.starting_resource_total == sum(sim.grid.resources_remaining.values())
