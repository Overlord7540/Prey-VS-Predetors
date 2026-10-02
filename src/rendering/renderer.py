"""
Draws the habitat full-bleed and floats the turn, the unit, and help on top.
Reads Simulation state only — never mutates it.
"""
from __future__ import annotations

import math
import textwrap
import pygame
from collections import deque

from src.core.simulation import Simulation
from src.rendering.identity import build_labels, describe_agent
from src.rendering.viewport import window_to_canvas
from src.rendering.camera import Camera
from src.rendering.chrome import INK, MOSS, MUTED, PAPER, SIGNAL, TRACK, card, round_rect
from src.rendering.sounds import play_cues
from src.rendering.asset_manager import (
    AssetManager,
    LEGEND_TILE_LABELS,
    LEGEND_TILE_ORDER,
)

def goal_sentence(sim) -> str:
    if getattr(sim, "kind", "") == "skirmish":
        return "Clear the other side."
    rules = sim.grid.rules
    taken = math.ceil(sim.starting_prey_count * rules.predator_win_prey_elimination_pct)
    eaten = math.ceil(sim.starting_resource_total * rules.prey_win_resource_pool_pct)
    return f"Hunters need {taken} taken down. The herd needs {eaten} eaten."


def goal_alpha(age: float, hold: float = 4.2, fade: float = 0.8) -> int:
    if age < hold:
        return 255
    if age >= hold + fade:
        return 0
    return round(255 * (1 - (age - hold) / fade))


LESSONS = {
    "glade": "Pale tiles are as far as the selected animal can walk. E ends your turn.",
    "rocks": "Stone blocks sight. Dim ground is hidden from the animal that is moving.",
    "ford": "A straight step costs 1. A diagonal costs 2. A buffalo can wade the river.",
    "rookery": "The hare spooks early. The heron sees farther than it can step. Jackals hunt as a pair.",
}

TILE_SIZE = 32
UI_HEIGHT = 80
LEGEND_WIDTH = 320


class Renderer:
    def __init__(self, sim: Simulation, assets: AssetManager):
        self.sim = sim
        self.labels = build_labels(sim.predators + sim.prey)
        self.assets = assets
        self.debug_overlay = False
        self.detailed = True
        self.text_items = []
        self.font_cache = {}
        self.selected_agent_id = None
        self.show_grid = False
        self.show_help = False
        self.clearing_index = 0
        self.duel_index = 1
        self.start_name = "noon"
        self.hovered_tile = None
        self.playback_speed = 1.0
        self.hit_stop = 0.0
        self.goal_age = 0.0
        self.shake = 0.0
        self._shake_clock = 0.0
        self.player_message = ""
        self.effects = []
        self.recent_events = deque(maxlen=3)
        self.camera = Camera(sim.grid.width, sim.grid.height)
        self.command_preview = ""
        self.attack_confirmation = False
        self.map_text_count = 0
        self._field = None
        self._field_size = None

    def queue_text(self, text, color, pos, size=14, bold=False, alpha=255, centered=False):
        self.text_items.append((text, color, pos, size, bold, alpha, centered))

    def draw_text(self, screen, viewport):
        """Rasterize fonts at the final window resolution, after scaling terrain."""
        scale = viewport.width / self.screen_size()[0]
        scale_y = viewport.height / self.screen_size()[1]
        previous_clip = screen.get_clip()
        screen.set_clip(viewport)
        for index, (text, color, pos, size, bold, alpha, centered) in enumerate(self.text_items):
            screen.set_clip(pygame.Rect(viewport.x, viewport.y, round(self.camera.width*scale), round(self.camera.height*scale_y)) if index < self.map_text_count else viewport)
            pixel_size = max(8, round(size * scale))
            key = (pixel_size, bold)
            if key not in self.font_cache:
                if len(self.font_cache) >= 128:
                    self.font_cache.clear()
                self.font_cache[key] = pygame.font.SysFont("georgia" if size >= 27 else "tahoma", pixel_size, bold=bold)
            label = self.font_cache[key].render(text, True, color)
            label.set_alpha(alpha)
            x = viewport.x + round(pos[0] * scale)
            y = viewport.y + round(pos[1] * scale_y)
            rect = label.get_rect(center=(x, y)) if centered else label.get_rect(topleft=(x, y))
            screen.blit(label, rect)
        screen.set_clip(previous_clip)

    def capture_events(self) -> None:
        for event in self.sim.events:
            self.effects.append([event, 0.0])
            self.recent_events.appendleft(event)
            if event.kind == "kill":
                self.hit_stop = max(self.hit_stop, 0.18)
                self.shake = min(1.0, self.shake + 0.7)
            elif event.kind == "hit" and event.damage > 0:
                self.hit_stop = max(self.hit_stop, 0.1)
                self.shake = min(1.0, self.shake + 0.35)
        play_cues(self.sim.events, getattr(self.sim, "last_action", None))

    def update(self, dt: float) -> None:
        if self.hit_stop > 0:
            self.hit_stop = max(0.0, self.hit_stop - dt)
            return
        self.goal_age += dt
        self.camera.follow(dt)
        self.shake = max(0.0, self.shake - 1.6 * dt)
        self._shake_clock += dt * 40
        for effect in self.effects:
            effect[1] += dt
        self.effects = [effect for effect in self.effects if effect[1] < 2.0]

    def shake_offset(self) -> tuple[int, int]:
        if self.shake <= 0:
            return 0, 0
        magnitude = self.shake * self.shake * 5
        return (round(math.sin(self._shake_clock) * magnitude),
                round(math.cos(self._shake_clock * 1.3) * magnitude))

    def screen_size(self) -> tuple[int, int]:
        return (self.camera.width + LEGEND_WIDTH, self.camera.height + UI_HEIGHT)

    def blit_map(self, surface, world):
        scaled = pygame.transform.scale(world, (self.sim.grid.width*self.camera.tile_size, self.sim.grid.height*self.camera.tile_size))
        clip = surface.get_clip()
        surface.set_clip((0, 0, self.camera.width, self.camera.height))
        ox, oy = self.camera.origin()
        sx, sy = self.shake_offset()
        surface.blit(scaled, (ox - self.camera.x + sx, oy - self.camera.y + sy))
        surface.set_clip(clip)

    def handle_debug_toggle(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self.debug_overlay = not self.debug_overlay

    def draw(self, surface: pygame.Surface) -> None:
        self.text_items.clear()
        self._paint_field(surface)
        world = pygame.Surface((self.sim.grid.width*TILE_SIZE, self.sim.grid.height*TILE_SIZE))
        self._draw_tiles(world)
        self._draw_agents(world)
        if self.detailed and self.sim.active_agent_id and not self.sim.human_turn:
            agent = next((a for a in self.sim.predators + self.sim.prey
                          if a.agent_id == self.sim.active_agent_id), None)
            if agent:
                r, c = agent.pos
                pygame.draw.rect(world, (255, 245, 120),
                                 (c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE), 3)
        self._draw_effects(world)
        if getattr(self.sim, "lesson", "") == "rocks":
            self._draw_sight_fog(world)
        if self.debug_overlay:
            self._draw_debug_overlay(world)
        sx, sy = self.shake_offset()
        zoom = self.camera.tile_size / TILE_SIZE
        ox, oy = self.camera.origin()
        self.text_items = [(t, c, (p[0] * zoom - self.camera.x + ox + sx, p[1] * zoom - self.camera.y + oy + sy), s, b, a, z)
                           for t, c, p, s, b, a, z in self.text_items]
        self.map_text_count = len(self.text_items)
        self.blit_map(surface, world)
        self._draw_goal(surface)
        self._draw_hud(surface)
        self._draw_play_notes(surface)

    def _draw_sight_fog(self, surface: pygame.Surface) -> None:
        actor_id = self.sim.active_agent_id
        if not actor_id:
            actor = next((unit for unit in self.sim.predators + self.sim.prey if unit.alive), None)
            actor_id = actor.agent_id if actor else None
        if not actor_id:
            return
        try:
            visible = set(self.sim.observe(actor_id).visible)
        except ValueError:
            return
        fog = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        fog.fill((8, 12, 20, 110))
        for row in range(self.sim.grid.height):
            for col in range(self.sim.grid.width):
                if (row, col) not in visible:
                    surface.blit(fog, (col * TILE_SIZE, row * TILE_SIZE))

    def _draw_goal(self, surface: pygame.Surface) -> None:
        alpha = goal_alpha(self.goal_age)
        if alpha <= 0:
            return
        sentence = goal_sentence(self.sim)
        banner = pygame.Rect(0, 16, min(680, self.camera.width - 48), 40)
        banner.centerx = self.camera.width // 2
        plate = pygame.Surface((banner.width, banner.height), pygame.SRCALPHA)
        pygame.draw.rect(plate, (*PAPER, alpha), plate.get_rect(), border_radius=12)
        surface.blit(plate, banner.topleft)
        self.queue_text(sentence, INK, (banner.x + 16, banner.y + 11), size=15, alpha=alpha)

    def _notes_rect(self) -> pygame.Rect:
        """The decision book sits in the legend, under the command button, off the board."""
        button_bottom = self.unit_card_rect().bottom + 16 + 48
        top = button_bottom + 16
        return pygame.Rect(self.camera.width + 16, top, LEGEND_WIDTH - 32, self.camera.height - top - 16)

    def _draw_play_notes(self, surface: pygame.Surface) -> None:
        briefing = getattr(self.sim, "briefing", None)
        lesson = LESSONS.get(getattr(self.sim, "lesson", ""), "")
        if briefing is None and not lesson:
            return
        panel = self._notes_rect()
        card(surface, panel, PAPER, radius=16)
        y = panel.y + 14
        if briefing is not None:
            self.queue_text(briefing.mind, INK, (panel.x + 16, y), size=16, bold=True)
            y += 24
            if not self.sim.human_turn:
                label = self.labels.get(briefing.actor_id, briefing.actor_id)
                for line in textwrap.wrap(f"{label}: {briefing.step}", width=32)[:2]:
                    self.queue_text(line, INK, (panel.x + 16, y), size=13)
                    y += 16
                y += 6
        if lesson and (briefing is None or self.sim.human_turn):
            for line in textwrap.wrap(lesson, width=32)[:3]:
                self.queue_text(line, INK, (panel.x + 16, y), size=13)
                y += 16
            y += 6
        if briefing is None:
            return
        for line in textwrap.wrap(briefing.seen, width=32)[:2]:
            self.queue_text(line, MUTED, (panel.x + 16, y), size=13)
            y += 16
        declined = textwrap.wrap(briefing.declined, width=32)
        if declined:
            self.queue_text(declined[0], MOSS, (panel.x + 16, y + 8), size=13)

    def _draw_tiles(self, surface: pygame.Surface) -> None:
        grid = self.sim.grid
        for r in range(grid.height):
            for c in range(grid.width):
                stock = grid.resources_remaining.get((r, c))
                rect = pygame.Rect(c*TILE_SIZE, r*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                surface.blit(self.assets.get_tile(grid.tiles[r][c], TILE_SIZE,
                             variant=(r*7+c*13) % 4, depleted=stock == 0), rect)
                if getattr(self.sim, "kind", "") == "skirmish" and grid.tiles[r][c] == "chokepoint":
                    pygame.draw.rect(surface, (232, 84, 42), rect, 3)
                if self.show_grid:
                    pygame.draw.rect(surface, (32, 58, 36), rect, 1)
                if stock is not None:
                    capacity = grid.tile_props((r, c)).resource_value
                    for i in range(capacity):
                        pygame.draw.rect(surface, (32, 39, 31), (rect.x+3+i*8, rect.bottom-5, 7, 4))
                        pygame.draw.rect(surface, (231, 204, 112) if i < stock else (104, 93, 63),
                                         (rect.x+4+i*8, rect.bottom-4, 5, 2))

    def _draw_effects(self, surface: pygame.Surface) -> None:
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for event, age in self.effects:
            r, c = event.pos
            center = (c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2)
            alpha = int(255 * (1.0 - age / 2.0))
            color = (255, 75, 65) if event.kind in ("kill", "hit") else (255, 220, 120)
            pygame.draw.circle(layer, (*color, alpha), center, 12 + int(age * 5), 2)
            if event.kind == "kill":
                x, y = center
                pygame.draw.line(layer, (*color, alpha), (x - 7, y - 7), (x + 7, y + 7), 3)
                pygame.draw.line(layer, (*color, alpha), (x - 7, y + 7), (x + 7, y - 7), 3)
            if event.kind in ("kill", "hit") and event.damage > 0:
                text = f"-{event.damage}"
                label_x = max(0, min(center[0] - 8, self.sim.grid.width * TILE_SIZE - 28))
                self.queue_text(text, color, (label_x, max(0, center[1] - 28 - int(age * 10))),
                                size=18, bold=True, alpha=alpha)
            if event.kind == "fled":
                self.queue_text("Fled", (186, 214, 160), (center[0] - 14, max(0, center[1] - 22 - int(age * 8))),
                                size=16, bold=True, alpha=alpha)
        surface.blit(layer, (0, 0))

    def _draw_agents(self, surface: pygame.Surface) -> None:
        for agent in self.sim.predators + self.sim.prey:
            if not agent.alive:
                continue
            x, y = agent.pos[1]*TILE_SIZE, agent.pos[0]*TILE_SIZE
            # A small team marker and ID leave the silhouette unobstructed.
            surface.blit(self.assets.get_sprite(agent.species, TILE_SIZE, include_label=False), (x, y))
            label = self.labels[agent.agent_id]
            tag = pygame.Rect(x + 1, y + 21, max(16, len(label) * 6 + 6), 11)
            round_rect(surface, PAPER if agent.side == "prey" else SIGNAL, tag, radius=3)
            self.queue_text(label, INK if agent.side == "prey" else PAPER, (x + 4, y + 21), size=10, bold=True)

    def _paint_field(self, surface: pygame.Surface) -> None:
        size = surface.get_size()
        if self._field is None or self._field_size != size:
            field = pygame.Surface(size)
            tile = 32
            for y in range(0, size[1], tile):
                for x in range(0, size[0], tile):
                    field.blit(self.assets.get_tile("open_field", tile, variant=(x // tile + y // tile) % 4), (x, y))
            wash = pygame.Surface(size, pygame.SRCALPHA)
            wash.fill((18, 40, 28, 36))
            field.blit(wash, (0, 0))
            self._field = field
            self._field_size = size
        surface.blit(self._field, (0, 0))

    def _rail(self):
        width, _height = self.screen_size()
        return pygame.Rect(width - 24 - 440, 24, 440, 0)

    def _status_rect(self):
        rail = self._rail()
        return pygame.Rect(rail.x, 24, rail.width, 108)

    def unit_card_rect(self):
        rail = self._rail()
        return pygame.Rect(rail.x, 148, rail.width, 276)

    def _draw_meter(self, surface, origin, label, value, target, width=168):
        self.queue_text(f"{label}  {value}/{target}", INK, origin, size=13)
        track = pygame.Rect(origin[0], origin[1] + 18, width, 8)
        round_rect(surface, TRACK, track, radius=4)
        span = max(target, 1)
        fill = track.copy()
        fill.width = max(0, min(track.width, round(track.width * value / span)))
        if fill.width:
            round_rect(surface, MOSS if label.startswith("Food") else SIGNAL, fill, radius=4)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        sim = self.sim
        status = self._status_rect()
        card(surface, status, PAPER, radius=22)
        phase = "Your turn" if sim.human_turn else sim.phase
        if sim.winner:
            if getattr(sim, "kind", "") == "skirmish":
                yours = {"predator": "hunter", "prey": "herd"}.get(sim.player_side)
                pack = "Tiger pack" if sim.winner == "hunter" else "Jackals"
                phase = "Victory" if yours == sim.winner else ("Defeat" if yours else f"{pack} victory")
            else:
                phase = ("Victory" if sim.winner == sim.player_side else "Defeat") if sim.player_side else sim.winner.capitalize() + " victory"
        self.queue_text(str(sim.turn), INK, (status.x + 22, status.y + 18), size=36, bold=True)
        self.queue_text(phase, MOSS if sim.human_turn else MUTED, (status.x + 96, status.y + 18), size=18, bold=True)
        facing = getattr(sim, "opponent_label", "")
        meter_y = status.y + 62
        if facing:
            self.queue_text(f"Facing {facing}", MUTED, (status.x + 96, status.y + 42), size=14)
            meter_y = status.y + 68
        if getattr(sim, "kind", "") == "skirmish":
            goals = (
                ("Tiger pack", sum(unit.alive for unit in sim.predators), len(sim.predators)),
                ("Jackals", sum(unit.alive for unit in sim.prey), len(sim.prey)),
            )
        else:
            killed = sim.starting_prey_count - sum(prey.alive for prey in sim.prey)
            eaten = sim.starting_resource_total - sum(sim.grid.resources_remaining.values())
            goals = (
                ("Prey defeated", killed, math.ceil(sim.starting_prey_count * sim.grid.rules.predator_win_prey_elimination_pct)),
                ("Food gathered", eaten, math.ceil(sim.starting_resource_total * sim.grid.rules.prey_win_resource_pool_pct)),
            )
        self._draw_meter(surface, (status.x + 22, meter_y), *goals[0], width=186)
        self._draw_meter(surface, (status.x + 230, meter_y), *goals[1], width=186)

        panel = self.unit_card_rect()
        card(surface, panel, PAPER, radius=22)
        actor_id = self.selected_agent_id or sim.active_agent_id
        agent = next((unit for unit in sim.predators + sim.prey if unit.agent_id == actor_id and unit.alive), None)
        if agent:
            surface.blit(self.assets.get_sprite(agent.species, 64, include_label=False), (panel.x + 18, panel.y + 18))
            self.queue_text(self.labels[agent.agent_id], INK, (panel.x + 98, panel.y + 22), size=22, bold=True)
            self.queue_text(agent.species, MUTED, (panel.x + 98, panel.y + 50), size=15)
            if getattr(sim, "kind", "") == "skirmish" or agent.side == "prey":
                self._draw_meter(surface, (panel.x + 98, panel.y + 78), "Health", agent.hp, agent.max_hp)
            else:
                intent = agent.intent.name.title() if agent.intent else "Hunt"
                self.queue_text(intent, MOSS, (panel.x + 98, panel.y + 78), size=15, bold=True)
            reason = self.command_preview or sim.decision_reasons.get(agent.agent_id, "Choose a tile, then an action.")
        else:
            self.queue_text("No unit selected", INK, (panel.x + 20, panel.y + 28), size=22, bold=True)
            reason = "Click one of your animals." if sim.human_turn else "The match is playing."
        for index, line in enumerate(textwrap.wrap(reason, width=34)[:4]):
            self.queue_text(line, MUTED, (panel.x + 20, panel.y + 168 + index * 20), size=14)

    def help_rect(self):
        return self.unit_card_rect()

    def draw_help(self, surface):
        """Reference information replaces the unit card until H is pressed again."""
        if not self.show_help:
            return
        rect = self.help_rect()
        self.text_items = [item for item in self.text_items if not rect.collidepoint(item[2])]
        card(surface, rect, INK, radius=22)
        self.queue_text("Field guide", PAPER, (rect.x + 18, rect.y + 16), size=20, bold=True)
        self.queue_text("H closes", PAPER, (rect.right - 18, rect.y + 22), size=13, centered=True)
        for i, name in enumerate(LEGEND_TILE_ORDER):
            y = rect.y + 52 + i * 22
            surface.blit(self.assets.get_tile(name, 16), (rect.x + 18, y))
            self.queue_text(LEGEND_TILE_LABELS[name], PAPER, (rect.x + 42, y), size=13)
        for i, line in enumerate(("Click a tile, then Attack, Feed, or Wait", "Esc cancels    E ends the turn", "Z zoom    Arrows pan    C focus", "H closes this guide")):
            self.queue_text(line, PAPER, (rect.x + 18, rect.y + 188 + i * 18), size=12)

    def _draw_debug_overlay(self, surface: pygame.Surface) -> None:
        focus = self._debug_focus()
        if focus is not None:
            observation = self.sim.observe(focus.agent_id)
            visible = set(observation.visible)
            fog = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            fog.fill((8, 12, 20, 110))
            heat = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            peak = max(observation.influence.values(), default=1) or 1
            tint = (176, 64, 64) if focus.side == "prey" else (64, 112, 176)
            for row in range(self.sim.grid.height):
                for col in range(self.sim.grid.width):
                    if (row, col) not in visible:
                        surface.blit(fog, (col * TILE_SIZE, row * TILE_SIZE))
            for (row, col), value in observation.influence.items():
                heat.fill((*tint, int(36 + 140 * value / peak)))
                surface.blit(heat, (col * TILE_SIZE, row * TILE_SIZE))
        for pred in self.sim.predators:
            if not pred.alive:
                continue
            label = f"{self.labels[pred.agent_id]} intent={pred.intent.name if pred.intent else '-'}"
            self.queue_text(label, (255, 0, 0), (pred.pos[1] * TILE_SIZE, pred.pos[0] * TILE_SIZE - 12), size=12, bold=False)
        for prey_unit in self.sim.prey:
            if not prey_unit.alive:
                continue
            label = prey_unit.state.name[:1]
            self.queue_text(label, (0, 255, 0), (prey_unit.pos[1] * TILE_SIZE, prey_unit.pos[0] * TILE_SIZE - 12), size=12, bold=False)

    def _debug_focus(self):
        living = [agent for agent in self.sim.predators + self.sim.prey if agent.alive]
        if self.sim.active_agent_id:
            active = next((agent for agent in living if agent.agent_id == self.sim.active_agent_id), None)
            if active is not None:
                return active
        if self.selected_agent_id:
            selected = next((agent for agent in living if agent.agent_id == self.selected_agent_id), None)
            if selected is not None:
                return selected
        return living[0] if living else None

    def draw_hover(self, screen, viewport, mouse_pos):
        logical = window_to_canvas(mouse_pos, self.screen_size(), screen.get_size())
        if logical is None:
            return
        x, y = logical
        tile = self.camera.tile_at(logical)
        if tile is None:
            return
        agent = next((a for a in self.sim.predators + self.sim.prey
                      if a.alive and a.pos == tile), None)
        if agent is None:
            return
        # Draw the inspection panel last, at native resolution, above all labels.
        font = pygame.font.SysFont("tahoma", 14)
        description = describe_agent(agent, self.labels[agent.agent_id])
        if agent.agent_id in self.sim.decision_reasons:
            description += textwrap.wrap("Last decision: " + self.sim.decision_reasons[agent.agent_id], width=max(20, min(48, (screen.get_width()-24)//8)))
        lines = [font.render(line, True, INK) for line in description]
        width = max(line.get_width() for line in lines) + 20
        height = len(lines) * 20 + 16
        left = max(0, min(mouse_pos[0] + 16, screen.get_width() - width))
        top = max(0, min(mouse_pos[1] + 18, screen.get_height() - height))
        panel = pygame.Rect(left, top, width, height)
        card(screen, panel, PAPER, radius=12)
        for i, line in enumerate(lines):
            screen.blit(line, (left + 10, top + 8 + i * 20))
