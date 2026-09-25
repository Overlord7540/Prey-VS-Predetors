"""
Floating combat text and simple particle effects. Deferred to the polish
phase (Phase 3) - kept minimal here so the interface exists for
simulation.py's combat events to hook into once built out.
"""
from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class FloatingText:
    text: str
    x: float
    y: float
    life: float = 1.0
    color: tuple = (255, 60, 60)

    def update(self, dt: float) -> None:
        self.y -= 20 * dt
        self.life -= dt

    def draw(self, surface: pygame.Surface) -> None:
        font = pygame.font.SysFont("consolas", 16, bold=True)
        alpha = max(0, min(255, int(255 * self.life)))
        surf = font.render(self.text, True, self.color)
        surf.set_alpha(alpha)
        surface.blit(surf, (self.x, self.y))


class ParticleSystem:
    def __init__(self):
        self.floating_texts: list[FloatingText] = []

    def spawn_damage_text(self, x: float, y: float, amount: int) -> None:
        self.floating_texts.append(FloatingText(text=f"-{amount} HP", x=x, y=y))

    def update(self, dt: float) -> None:
        for t in self.floating_texts:
            t.update(dt)
        self.floating_texts = [t for t in self.floating_texts if t.life > 0]

    def draw(self, surface: pygame.Surface) -> None:
        for t in self.floating_texts:
            t.draw(surface)
