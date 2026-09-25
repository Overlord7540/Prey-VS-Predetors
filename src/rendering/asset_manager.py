"""
Loads sprites/audio if present under assets/, otherwise falls back to a
flat-colored square/circle so the game is fully playable with zero art.
Swap in real sprites later without touching any game logic.
"""
from __future__ import annotations

from pathlib import Path

import pygame

ASSET_DIR = Path(__file__).resolve().parents[2] / "assets"

FALLBACK_COLORS = {
    "tiger": (230, 126, 34),
    "wolf": (127, 140, 141),
    "deer": (210, 180, 140),
    "buffalo": (101, 67, 33),
    "giraffe": (241, 196, 15),
    "open_field": (144, 195, 115),
    "feeding_ground": (196, 219, 90),
    "resource_node": (255, 215, 0),
    "river": (64, 128, 200),
    "chokepoint": (100, 160, 220),
    "rock": (120, 120, 120),
}


class AssetManager:
    def __init__(self):
        self._cache: dict[str, pygame.Surface] = {}

    def get_sprite(self, name: str, size: int) -> pygame.Surface:
        key = f"{name}_{size}"
        if key in self._cache:
            return self._cache[key]

        path = ASSET_DIR / "sprites" / f"{name}.png"
        if path.exists():
            surf = pygame.image.load(str(path)).convert_alpha()
            surf = pygame.transform.smoothscale(surf, (size, size))
        else:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            color = FALLBACK_COLORS.get(name, (200, 50, 200))
            pygame.draw.circle(surf, color, (size // 2, size // 2), size // 2 - 2)

        self._cache[key] = surf
        return surf

    def get_tile_color(self, tile_name: str) -> tuple:
        return FALLBACK_COLORS.get(tile_name, (50, 50, 50))
