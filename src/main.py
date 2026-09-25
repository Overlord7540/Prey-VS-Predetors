"""
Entry point. Loads config, spawns a default scenario, and runs the
Pygame loop (Input -> Update -> Draw) per the tech spec's execution flow.

Run with:  python -m src.main
"""
from __future__ import annotations

import random

import pygame

from src.ai.fsm import roll_intent
from src.core.agent import Flock, PredatorAgent, PreyAgent
from src.core.grid import Grid
from src.core.simulation import Simulation
from src.data.loader import load_map, load_tiles, load_units
from src.rendering.asset_manager import AssetManager
from src.rendering.renderer import Renderer

STEP_EVERY_MS = 500  # one simulation turn every N ms, so it's watchable


def build_default_scenario() -> Simulation:
    units = load_units()
    tiles = load_tiles()
    game_map = load_map()
    grid = Grid(game_map, tiles)

    predators = [
        PredatorAgent(agent_id="tiger_1", species="tiger", pos=(5, 5), side="predator"),
        PredatorAgent(agent_id="wolf_1", species="wolf", pos=(14, 14), side="predator"),
        PredatorAgent(agent_id="wolf_2", species="wolf", pos=(14, 15), side="predator"),
    ]
    for p in predators:
        p.intent = roll_intent(p.species)

    flock = Flock(flock_id="deer_herd", member_ids=[f"deer_{i}" for i in range(5)])
    prey = [
        PreyAgent(
            agent_id=f"deer_{i}", species="deer", side="prey",
            pos=(random.randint(0, 3), random.randint(0, 3)),
            hp=units["deer"].hp, max_hp=units["deer"].hp, flock_id=flock.flock_id,
        )
        for i in range(5)
    ]

    return Simulation(
        grid=grid, unit_stats=units, predators=predators, prey=prey,
        flocks={flock.flock_id: flock},
    )


def main() -> None:
    pygame.init()
    sim = build_default_scenario()
    assets = AssetManager()
    renderer = Renderer(sim, assets)

    screen = pygame.display.set_mode(renderer.screen_size())
    pygame.display.set_caption("Predator & Prey - Tactical AI Simulation")
    clock = pygame.time.Clock()

    time_since_step = 0
    running = True
    while running:
        dt = clock.tick(60)
        time_since_step += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            renderer.handle_debug_toggle(event)

        if not sim.is_over() and time_since_step >= STEP_EVERY_MS:
            sim.step()
            time_since_step = 0

        renderer.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
