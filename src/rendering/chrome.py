"""Paint tokens for the meadow screen. The simulation never imports this."""
import pygame

INK = (20, 36, 28)
PAPER = (246, 248, 240)
MOSS = (36, 92, 58)
SIGNAL = (232, 84, 42)
MUTED = (86, 102, 84)
TRACK = (214, 222, 206)


def round_rect(surface, color, rect, radius=16, width=0):
    pygame.draw.rect(surface, color, rect, width, border_radius=radius)


def card(surface, rect, fill=PAPER, radius=18):
    shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (16, 32, 22, 72), shadow.get_rect(), border_radius=radius)
    surface.blit(shadow, (rect.x + 4, rect.y + 6))
    round_rect(surface, fill, rect, radius)
