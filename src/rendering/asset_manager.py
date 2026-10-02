"""Cached 32-pixel wildlife art, terrain, and optional sprite overrides."""
from __future__ import annotations

import pygame

from src.rendering.pixel_art import SPRITES, animal_surface, terrain_surface
from src.root import project_root

ASSET_DIR = project_root() / "assets"


def _clear_backdrop(surface):
    """Tiny Creatures stores the empty margin as opaque black."""
    cleared = surface.copy()
    for y in range(cleared.get_height()):
        for x in range(cleared.get_width()):
            red, green, blue, alpha = cleared.get_at((x, y))
            if red < 12 and green < 12 and blue < 12:
                cleared.set_at((x, y), (0, 0, 0, 0))
    return cleared


def _depleted(surface):
    faded = surface.copy()
    for y in range(faded.get_height()):
        for x in range(faded.get_width()):
            red, green, blue, alpha = faded.get_at((x, y))
            if alpha:
                faded.set_at((x, y), (red // 3, green // 3, blue // 4, alpha))
    return faded


def _scale_nearest(surface, size: int):
    """Scale by a whole number. 32 masters become 32, 64, or 96, never a fraction."""
    width, height = surface.get_size()
    if width == size and height == size:
        return surface
    factor = max(1, int(round(size / width)))
    if width * factor != size:
        factor = max(1, size // width)
    return pygame.transform.scale(surface, (width * factor, height * factor))

# Shared colors for interface swatches. Identity is also carried by silhouettes
# and external letter/number badges, never by color alone.
FALLBACK_COLORS = {
    "tiger": (209, 133, 62),
    "wolf": (135, 153, 164),
    "deer": (179, 129, 84),
    "buffalo": (153, 138, 116),
    "giraffe": (221, 181, 99),
    "open_field": (113, 131, 84),
    "feeding_ground": (140, 155, 98),
    "resource_node": (85, 119, 69),
    "river": (65, 109, 130),
    "chokepoint": (167, 166, 136),
    "rock": (156, 157, 134),
}

# Single-letter labels drawn on top of each agent sprite so identity never
# depends on color alone (helps with colorblindness and small screens).
AGENT_LABELS = {
    "tiger": "T",
    "wolf": "W",
    "deer": "D",
    "buffalo": "B",
    "giraffe": "G",
}

LEGEND_ORDER = ["tiger", "wolf", "deer", "buffalo", "giraffe"]
LEGEND_TILE_ORDER = ["open_field", "feeding_ground", "resource_node", "river", "chokepoint", "rock"]
LEGEND_TILE_LABELS = {
    "open_field": "Open Field",
    "feeding_ground": "Feeding Ground",
    "resource_node": "Resource Node",
    "river": "River",
    "chokepoint": "Chokepoint",
    "rock": "Rock",
}


class AssetManager:
    def __init__(self):
        self._cache: dict[str, pygame.Surface] = {}
        self._tile_cache: dict[tuple, pygame.Surface] = {}
        self._font_cache: dict[int, pygame.font.Font] = {}

    def _font(self, size: int) -> pygame.font.Font:
        if size not in self._font_cache:
            self._font_cache[size] = pygame.font.SysFont("consolas", size, bold=True)
        return self._font_cache[size]

    def get_sprite(self, name: str, size: int, include_label: bool = True) -> pygame.Surface:
        if size < 1:
            raise ValueError("Sprite size must be positive")
        key = f"{name}_{size}_{include_label}"
        if key in self._cache:
            return self._cache[key]

        path = ASSET_DIR / "sprites" / f"{name}.png"
        if path.exists():
            surf = _clear_backdrop(pygame.image.load(str(path)).convert_alpha())
            surf = _scale_nearest(surf, size)
        elif name in SPRITES:
            surf = pygame.transform.scale(animal_surface(name), (size, size))
        else:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            color = FALLBACK_COLORS.get(name, (200, 50, 200))
            surf.fill(color)

        label = AGENT_LABELS.get(name)
        if label and include_label:
            # Kept for API compatibility. The game draws its own identity badge
            # at native window resolution, using include_label=False here.
            font = self._font(max(8, size // 3))
            text_surf = font.render(label, False, (242, 232, 202))
            text_rect = text_surf.get_rect(bottomright=(size - 1, size))
            pygame.draw.rect(surf, (23, 37, 32), text_rect.inflate(2, 0))
            surf.blit(text_surf, text_rect)

        self._cache[key] = surf
        return surf

    def get_tile(self, tile_name: str, size: int, variant: int = 0,
                 depleted: bool = False) -> pygame.Surface:
        """Return cached terrain; variants and depletion never alter rules."""
        if size < 1:
            raise ValueError("Tile size must be positive")
        key = (tile_name, size, variant % 4, depleted)
        if key not in self._tile_cache:
            variant_index = variant % 4
            path = ASSET_DIR / "tiles" / f"{tile_name}_{variant_index}.png"
            if not path.exists():
                path = ASSET_DIR / "tiles" / f"{tile_name}_0.png"
            if path.exists() and not depleted:
                source = pygame.image.load(str(path)).convert_alpha()
            elif path.exists():
                source = _depleted(pygame.image.load(str(path)).convert_alpha())
            else:
                source = terrain_surface(tile_name, variant, depleted)
            self._tile_cache[key] = _scale_nearest(source, size)
        return self._tile_cache[key]

    def get_tile_color(self, tile_name: str) -> tuple:
        return FALLBACK_COLORS.get(tile_name, (50, 50, 50))
