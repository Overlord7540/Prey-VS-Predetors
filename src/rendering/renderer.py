"""
Draws the grid, agents, and minimal UI. Reads Simulation state only -
never mutates it. Smooth interpolation and the debug overlay (F1) are
noted as TODOs; v1 renders discrete tile-snapped positions.
"""
from __future__ import annotations

import pygame

from src.core.simulation import Simulation
from src.rendering.asset_manager import AssetManager

TILE_SIZE = 28
UI_HEIGHT = 60


class Renderer:
    def __init__(self, sim: Simulation, assets: AssetManager):
        self.sim = sim
        self.assets = assets
        self.debug_overlay = False

    def screen_size(self) -> tuple[int, int]:
        return (self.sim.grid.width * TILE_SIZE, self.sim.grid.height * TILE_SIZE + UI_HEIGHT)

    def handle_debug_toggle(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self.debug_overlay = not self.debug_overlay

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((10, 10, 10))
        self._draw_tiles(surface)
        self._draw_agents(surface)
        self._draw_ui(surface)
        if self.debug_overlay:
            self._draw_debug_overlay(surface)

    def _draw_tiles(self, surface: pygame.Surface) -> None:
        grid = self.sim.grid
        for r in range(grid.height):
            for c in range(grid.width):
                color = self.assets.get_tile_color(grid.tiles[r][c])
                rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (0, 0, 0), rect, 1)

    def _draw_agents(self, surface: pygame.Surface) -> None:
        for pred in self.sim.predators:
            if not pred.alive:
                continue
            sprite = self.assets.get_sprite(pred.species, TILE_SIZE - 4)
            surface.blit(sprite, (pred.pos[1] * TILE_SIZE + 2, pred.pos[0] * TILE_SIZE + 2))

        for prey_unit in self.sim.prey:
            if not prey_unit.alive:
                continue
            sprite = self.assets.get_sprite(prey_unit.species, TILE_SIZE - 4)
            surface.blit(sprite, (prey_unit.pos[1] * TILE_SIZE + 2, prey_unit.pos[0] * TILE_SIZE + 2))

    def _draw_ui(self, surface: pygame.Surface) -> None:
        font = pygame.font.SysFont("consolas", 18)
        y = self.sim.grid.height * TILE_SIZE + 8
        alive = sum(1 for p in self.sim.prey if p.alive)
        resources = sum(self.sim.grid.resources_remaining.values())
        text = f"Turn {self.sim.turn}  |  Prey alive: {alive}/{self.sim.starting_prey_count}  |  Resources left: {resources}"
        surface.blit(font.render(text, True, (255, 255, 255)), (8, y))
        if self.sim.winner:
            banner = font.render(f"{self.sim.winner.upper()} WINS", True, (255, 60, 60))
            surface.blit(banner, (8, y + 22))

    def _draw_debug_overlay(self, surface: pygame.Surface) -> None:
        font = pygame.font.SysFont("consolas", 12)
        for pred in self.sim.predators:
            if not pred.alive:
                continue
            label = f"{pred.species[:1].upper()} intent={pred.intent.name if pred.intent else '-'}"
            surface.blit(font.render(label, True, (255, 0, 0)),
                         (pred.pos[1] * TILE_SIZE, pred.pos[0] * TILE_SIZE - 12))
        for prey_unit in self.sim.prey:
            if not prey_unit.alive:
                continue
            label = prey_unit.state.name[:1]
            surface.blit(font.render(label, True, (0, 255, 0)),
                         (prey_unit.pos[1] * TILE_SIZE, prey_unit.pos[0] * TILE_SIZE - 12))
