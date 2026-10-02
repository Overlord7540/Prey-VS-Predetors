"""Shared scenario builders and injected controllers for behavioral tests."""
from contextlib import contextmanager
from src.core.agent import Flock, PreyAgent
from src.core.grid import Grid
from src.core.simulation import Simulation
from src.core.control import Action
from src.data.loader import load_map, load_tiles, load_units


def make_sim(positions, predator=None):
    prey = [PreyAgent(str(i), "deer", pos, "prey", hp=40, max_hp=40, flock_id="f")
            for i, pos in enumerate(positions)]
    return Simulation(Grid(load_map(), load_tiles()), load_units(),
                      [predator] if predator else [], prey,
                      {"f": Flock("f", [p.agent_id for p in prey])})


class FixedController:
    def __init__(self, destination):
        self.destination = destination

    def choose_action(self, observation):
        return Action(self.destination)


@contextmanager
def fixed_move(sim, destination):
    old = dict(sim.controllers)
    sim.controllers["prey"] = FixedController(destination)
    try:
        yield
    finally:
        sim.controllers = old
