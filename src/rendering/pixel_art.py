"""Editable 32-pixel wildlife and terrain for the tactical board.

The small palette, stepped silhouettes and one-pixel details are intentional.
No filtering or random state is used when producing the source surfaces.
"""
from __future__ import annotations

import pygame


SPRITES = ("tiger", "wolf", "deer", "buffalo", "giraffe")
OUTLINE = (43, 42, 42)
SPRITE_PALETTES = {
    "tiger": {"a": (209, 133, 62), "b": (94, 58, 45), "h": (241, 180, 91), "e": (239, 220, 177)},
    "wolf": {"a": (135, 153, 164), "b": (78, 94, 113), "h": (189, 204, 208), "e": (222, 223, 205)},
    "deer": {"a": (179, 129, 84), "b": (116, 77, 58), "h": (222, 180, 125), "e": (240, 222, 180)},
    "buffalo": {"a": (110, 99, 91), "b": (69, 64, 67), "h": (153, 138, 116), "e": (222, 210, 174)},
    "giraffe": {"a": (221, 181, 99), "b": (130, 81, 53), "h": (247, 218, 145), "e": (240, 224, 189)},
}


def _shape(surface, color, points, outline=True):
    pygame.draw.polygon(surface, color, points)
    if outline:
        pygame.draw.lines(surface, OUTLINE, True, points, 1)


def _line(surface, color, points, width=1):
    pygame.draw.lines(surface, color, False, points, width)


def _tiger(surface, palette):
    base, shade, light, cream = (palette[key] for key in ("a", "b", "h", "e"))
    _line(surface, OUTLINE, [(7, 18), (3, 17), (2, 12), (3, 10)], 3)
    _line(surface, base, [(7, 18), (3, 17), (2, 12), (3, 10)])
    _shape(surface, shade, [(8, 21), (12, 21), (11, 28), (6, 28), (6, 26), (8, 25)])
    _shape(surface, shade, [(21, 20), (24, 21), (25, 27), (22, 28), (20, 27)])
    _shape(surface, base, [(5, 16), (8, 13), (18, 13), (23, 11), (27, 14),
                            (26, 21), (22, 24), (11, 24), (6, 22)])
    _shape(surface, light, [(8, 14), (18, 14), (21, 13), (23, 15), (21, 18),
                             (12, 18), (6, 20)], False)
    _shape(surface, cream, [(13, 22), (21, 21), (24, 18), (25, 21), (21, 24), (13, 24)], False)
    _shape(surface, base, [(8, 20), (12, 20), (12, 24), (10, 26), (10, 28),
                            (6, 28), (6, 26), (8, 24)])
    _shape(surface, base, [(19, 20), (23, 20), (22, 27), (24, 28), (24, 29),
                            (19, 29), (18, 27)])
    pygame.draw.rect(surface, cream, (7, 27, 3, 1))
    pygame.draw.rect(surface, cream, (20, 28, 3, 1))
    _shape(surface, shade, [(20, 12), (19, 9), (21, 8), (23, 10)])
    _shape(surface, shade, [(26, 10), (26, 8), (29, 8), (29, 12)])
    _shape(surface, light, [(21, 11), (24, 10), (28, 11), (29, 14), (30, 16),
                             (28, 19), (24, 20), (21, 17)])
    _shape(surface, cream, [(25, 15), (28, 15), (30, 16), (28, 18), (25, 18), (23, 16)], False)
    for points in ([(10, 14), (11, 18), (10, 20)], [(15, 14), (16, 17), (15, 19)],
                   [(19, 14), (19, 17), (18, 18)], [(7, 20), (9, 21)],
                   [(21, 21), (20, 23)], [(22, 12), (23, 14)], [(27, 11), (26, 13)]):
        _line(surface, shade, points)
    surface.set_at((27, 14), OUTLINE)
    pygame.draw.rect(surface, OUTLINE, (29, 16, 2, 1))
    surface.set_at((26, 18), shade)


def _wolf(surface, palette):
    base, shade, light, cream = (palette[key] for key in ("a", "b", "h", "e"))
    _shape(surface, shade, [(9, 18), (5, 16), (3, 12), (2, 15), (3, 20), (6, 23), (11, 22)])
    _line(surface, light, [(3, 14), (4, 18), (7, 20)])
    _shape(surface, shade, [(9, 22), (12, 23), (11, 27), (8, 28), (7, 27)])
    _shape(surface, shade, [(20, 20), (23, 20), (24, 27), (20, 28)])
    _shape(surface, base, [(7, 18), (10, 15), (17, 15), (21, 10), (25, 12),
                            (26, 17), (24, 18), (24, 22), (21, 21), (19, 24), (11, 24), (8, 22)])
    _shape(surface, light, [(9, 16), (17, 16), (20, 13), (23, 13), (21, 18),
                             (17, 19), (12, 18)], False)
    _shape(surface, cream, [(22, 17), (25, 17), (23, 21), (21, 20), (19, 23), (17, 23)], False)
    _shape(surface, base, [(9, 21), (12, 21), (13, 24), (11, 27), (12, 29),
                            (7, 29), (7, 27), (9, 25)])
    _shape(surface, base, [(20, 21), (23, 21), (22, 27), (24, 28), (24, 29),
                            (19, 29), (19, 26)])
    pygame.draw.rect(surface, cream, (8, 28, 3, 1))
    pygame.draw.rect(surface, cream, (20, 28, 3, 1))
    _shape(surface, shade, [(20, 12), (20, 5), (24, 10)])
    _shape(surface, base, [(24, 10), (27, 5), (28, 12)])
    _shape(surface, base, [(21, 10), (25, 9), (28, 13), (31, 14), (30, 17),
                            (26, 18), (22, 16), (20, 16)])
    _shape(surface, light, [(23, 10), (25, 10), (27, 13), (25, 14), (22, 13)], False)
    _shape(surface, cream, [(25, 14), (29, 14), (30, 15), (29, 17), (26, 17), (23, 15)], False)
    _line(surface, shade, [(22, 7), (22, 10)])
    surface.set_at((27, 13), OUTLINE)
    pygame.draw.rect(surface, OUTLINE, (30, 14, 2, 2))
    surface.set_at((28, 17), shade)


def _deer(surface, palette):
    base, shade, light, cream = (palette[key] for key in ("a", "b", "h", "e"))
    _shape(surface, shade, [(8, 21), (10, 21), (9, 28), (7, 29), (7, 27)])
    _shape(surface, shade, [(20, 20), (22, 20), (23, 28), (21, 28)])
    _shape(surface, cream, [(6, 18), (3, 15), (5, 15), (8, 17)])
    _shape(surface, base, [(6, 18), (9, 16), (17, 16), (20, 13), (21, 10),
                            (25, 11), (24, 17), (22, 22), (17, 24), (9, 24), (6, 21)])
    _shape(surface, light, [(8, 17), (17, 17), (20, 15), (22, 13), (22, 16),
                             (18, 20), (10, 19), (7, 20)], False)
    _shape(surface, cream, [(21, 15), (23, 14), (22, 19), (19, 22), (13, 23),
                             (9, 22), (16, 22)], False)
    _shape(surface, base, [(9, 21), (11, 22), (10, 26), (10, 29), (8, 29), (8, 27)])
    _shape(surface, base, [(18, 21), (20, 21), (20, 26), (19, 29), (17, 29), (18, 27)])
    pygame.draw.rect(surface, OUTLINE, (8, 29, 2, 1))
    pygame.draw.rect(surface, OUTLINE, (17, 29, 2, 1))
    _line(surface, shade, [(22, 10), (20, 7), (20, 3), (18, 2)])
    _line(surface, shade, [(20, 6), (17, 5), (17, 3)])
    _line(surface, shade, [(24, 10), (25, 7), (25, 2)])
    _line(surface, shade, [(25, 5), (28, 3), (28, 1)])
    _line(surface, cream, [(21, 7), (21, 4)])
    _line(surface, cream, [(26, 6), (26, 4)])
    _shape(surface, base, [(22, 11), (18, 8), (18, 11), (21, 13)])
    _shape(surface, light, [(24, 10), (28, 8), (27, 11), (25, 12)])
    _shape(surface, base, [(22, 10), (25, 10), (27, 13), (29, 14),
                            (29, 16), (26, 17), (23, 15), (21, 13)])
    _line(surface, cream, [(24, 14), (26, 16), (28, 16)])
    surface.set_at((26, 13), OUTLINE)
    surface.set_at((29, 15), OUTLINE)


def _buffalo(surface, palette):
    base, shade, light, cream = (palette[key] for key in ("a", "b", "h", "e"))
    _line(surface, OUTLINE, [(7, 17), (4, 18), (3, 23), (2, 24)], 2)
    _shape(surface, shade, [(10, 21), (13, 21), (12, 28), (9, 28)])
    _shape(surface, shade, [(22, 21), (25, 21), (26, 28), (22, 28)])
    _shape(surface, base, [(5, 16), (8, 12), (16, 10), (22, 11), (26, 15),
                            (27, 22), (23, 25), (10, 25), (6, 22)])
    _shape(surface, light, [(8, 13), (16, 11), (21, 12), (20, 16), (12, 17), (6, 18)], False)
    _shape(surface, shade, [(15, 21), (21, 18), (26, 20), (24, 24), (14, 24)], False)
    _shape(surface, base, [(7, 21), (12, 22), (11, 29), (6, 29), (6, 27)])
    _shape(surface, base, [(19, 22), (23, 22), (23, 29), (18, 29), (18, 27)])
    pygame.draw.rect(surface, shade, (7, 27, 4, 2))
    pygame.draw.rect(surface, shade, (19, 27, 3, 2))
    _shape(surface, shade, [(21, 13), (25, 12), (29, 15), (30, 21), (28, 24),
                             (25, 24), (22, 22), (20, 17)])
    _shape(surface, base, [(23, 14), (27, 14), (29, 18), (27, 20), (23, 18)], False)
    pygame.draw.rect(surface, light, (25, 21, 4, 2))
    _line(surface, OUTLINE, [(24, 14), (20, 13), (18, 10), (19, 8)], 3)
    _line(surface, cream, [(24, 13), (21, 12), (19, 10), (19, 8)])
    _line(surface, OUTLINE, [(26, 13), (29, 12), (30, 9), (29, 7)], 3)
    _line(surface, cream, [(26, 12), (29, 11), (29, 8)])
    surface.set_at((27, 17), cream)
    surface.set_at((28, 18), OUTLINE)
    surface.set_at((28, 22), OUTLINE)


def _giraffe(surface, palette):
    base, shade, light, cream = (palette[key] for key in ("a", "b", "h", "e"))
    _line(surface, OUTLINE, [(7, 19), (4, 21), (3, 25)], 1)
    pygame.draw.rect(surface, shade, (2, 24, 2, 3))
    _shape(surface, shade, [(10, 23), (12, 23), (11, 29), (9, 29)])
    _shape(surface, shade, [(20, 20), (22, 21), (23, 29), (21, 29)])
    _shape(surface, base, [(6, 20), (9, 17), (16, 17), (20, 7), (24, 7),
                            (22, 16), (21, 22), (16, 25), (8, 24)])
    _shape(surface, light, [(8, 19), (17, 18), (21, 8), (22, 8), (19, 20), (10, 21)], False)
    _shape(surface, cream, [(18, 21), (21, 18), (20, 22), (16, 24), (11, 24)], False)
    _shape(surface, base, [(8, 22), (11, 23), (10, 29), (8, 29)])
    _shape(surface, base, [(17, 22), (20, 21), (19, 29), (17, 29)])
    pygame.draw.rect(surface, OUTLINE, (8, 29, 2, 1))
    pygame.draw.rect(surface, OUTLINE, (17, 29, 2, 1))
    _line(surface, shade, [(21, 6), (21, 2)])
    _line(surface, shade, [(24, 6), (24, 2)])
    pygame.draw.rect(surface, OUTLINE, (20, 1, 2, 2))
    pygame.draw.rect(surface, OUTLINE, (24, 1, 2, 2))
    _shape(surface, base, [(21, 7), (18, 4), (18, 7), (20, 9)])
    _shape(surface, light, [(23, 6), (28, 4), (26, 8)])
    _shape(surface, base, [(21, 5), (25, 5), (26, 8), (29, 9), (29, 11),
                            (26, 12), (22, 9), (20, 8)])
    _line(surface, cream, [(25, 10), (28, 11)])
    for rect in ((9, 19, 3, 2), (14, 19, 2, 3), (18, 16, 2, 2),
                 (19, 12, 2, 2), (21, 9, 2, 2), (8, 23, 2, 2)):
        pygame.draw.rect(surface, shade, rect)
    surface.set_at((25, 8), OUTLINE)
    surface.set_at((29, 10), OUTLINE)


_ANIMAL_DRAWERS = {"tiger": _tiger, "wolf": _wolf, "deer": _deer,
                   "buffalo": _buffalo, "giraffe": _giraffe}


def animal_surface(name: str) -> pygame.Surface:
    """Return original 32-pixel art, without a label or team marker."""
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (37, 43, 39, 52), (4, 27, 23, 4))
    _ANIMAL_DRAWERS[name](surface, SPRITE_PALETTES[name])
    return surface


GRASS = (113, 131, 84)


def _grass(surface, variant):
    surface.fill(GRASS)
    for index in range(11):
        x = (index * 13 + variant * 5 + 2) % 31
        y = (index * 9 + variant * 11 + 3) % 31
        color = (122, 139, 91) if index % 3 else (104, 123, 78)
        pygame.draw.line(surface, color, (x, y), (min(31, x + 2), y))
        if index % 4 == 0:
            surface.set_at((min(31, x + 1), max(0, y - 1)), color)


def terrain_surface(name: str, variant: int = 0, depleted: bool = False) -> pygame.Surface:
    """Produce subdued terrain with deterministic spatial variation."""
    surface = pygame.Surface((32, 32))
    variant %= 4
    _grass(surface, variant)

    if name in ("river", "chokepoint"):
        surface.fill((65, 109, 130))
        for index, y in enumerate((4, 13, 23, 29)):
            x = (index * 11 + variant * 5) % 24
            length = 4 + index % 3
            pygame.draw.line(surface, (81, 125, 143), (x, y), (x + length, y))
            pygame.draw.line(surface, (60, 103, 125), (max(0, x - 4), y + 2), (x + 2, y + 2))
        if name == "chokepoint":
            for x, y, width, height in ((11, -2, 11, 8), (8, 9, 12, 7), (13, 21, 12, 8)):
                pygame.draw.ellipse(surface, (51, 93, 110), (x - 2, y + 2, width + 4, height + 2))
                _shape(surface, (167, 166, 136), [(x, y + 2), (x + 3, y), (x + width - 3, y),
                         (x + width, y + 2), (x + width - 1, y + height - 1), (x + 2, y + height)], False)
                pygame.draw.line(surface, (195, 190, 156), (x + 3, y + 1), (x + width - 3, y + 1))
                pygame.draw.line(surface, (123, 137, 125), (x + 2, y + height), (x + width - 2, y + height))
    elif name == "rock":
        pygame.draw.ellipse(surface, (91, 109, 76), (3, 21, 26, 7))
        _shape(surface, (109, 119, 111), [(4, 21), (8, 11), (15, 6), (23, 9),
                      (28, 19), (26, 24), (17, 27), (7, 25)], False)
        _shape(surface, (156, 157, 134), [(8, 11), (15, 6), (22, 9), (21, 16),
                      (12, 19), (5, 21)], False)
        _shape(surface, (126, 136, 122), [(21, 16), (23, 9), (28, 19), (25, 23), (19, 24)], False)
        _line(surface, (177, 175, 149), [(9, 11), (15, 8), (20, 9)])
        _line(surface, (92, 105, 99), [(12, 20), (18, 21), (21, 17)])
        _line(surface, (132, 145, 106), [(7, 25), (11, 26), (15, 25)])
    elif name in ("feeding_ground", "resource_node"):
        if depleted:
            for x, y, width in ((7, 12, 7), (16, 18, 9), (6, 23, 7)):
                pygame.draw.line(surface, (123, 121, 83), (x, y), (x + width, y), 2)
                pygame.draw.line(surface, (146, 139, 97), (x + 2, y + 1), (x + width - 2, y + 1))
                surface.set_at((x + 1, y - 1), (100, 113, 75))
        elif name == "feeding_ground":
            offsets = ((0, 0), (2, -1), (-1, 1), (1, 2))
            dx, dy = offsets[variant]
            for x, y in ((8, 13), (18, 10), (24, 22), (12, 25), (17, 19)):
                x, y = x + dx, y + dy
                _line(surface, (87, 113, 67), [(x - 3, y), (x, y + 1), (x + 3, y)])
                _line(surface, (140, 155, 98), [(x - 2, y - 3), (x, y), (x, y - 5)])
                _line(surface, (151, 161, 103), [(x, y), (x + 3, y - 4)])
        else:
            pygame.draw.ellipse(surface, (88, 107, 70), (6, 21, 23, 7))
            pygame.draw.rect(surface, (110, 101, 71), (16, 18, 3, 8))
            _shape(surface, (68, 99, 63), [(5, 19), (6, 13), (10, 12), (10, 8),
                  (17, 6), (23, 9), (24, 13), (28, 15), (27, 21), (23, 24), (12, 24)], False)
            _shape(surface, (85, 119, 69), [(7, 16), (11, 14), (12, 10), (18, 8),
                  (22, 11), (22, 15), (25, 17), (21, 21), (13, 20), (8, 22)], False)
            _line(surface, (116, 140, 83), [(12, 11), (16, 10), (19, 11)])
            _line(surface, (116, 140, 83), [(8, 17), (11, 16), (14, 17)])
            _line(surface, (105, 132, 76), [(17, 18), (20, 17), (23, 18)])
            for x, y in ((12, 16), (20, 12), (22, 20)):
                pygame.draw.rect(surface, (150, 97, 66), (x, y, 2, 2))
                surface.set_at((x, y), (187, 128, 76))
    return surface
