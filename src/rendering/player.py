"""Player selection and tactical display; simulation owns action validation."""
import pygame
from src.core.control import Action
from src.rendering.chrome import INK, PAPER, card
from src.rendering.renderer import TILE_SIZE


class PlayerView:
    def __init__(self, sim, renderer=None):
        self.sim = sim
        self.selected = None
        self.renderer = renderer
        self.destination = None
        self.target_id = None
        self.attacking = False
        self.message = "Select an animal, click a tile, then choose a command."

    def reset(self):
        self.selected = self.destination = self.target_id = None
        self.attacking = False

    def planned_position(self):
        return self.destination or self.sim.observe(self.selected).actor.pos

    def targets(self):
        return self.sim.attack_targets(self.selected, self.planned_position()) if self.selected else []

    def attack(self):
        targets = self.targets()
        if not targets:
            return False
        if self.target_id:
            return self.commit(self.planned_position(), "attack", self.target_id)
        self.attacking = True
        self.message = "Click the animal to strike. Esc cancels."
        return False

    def cancel(self):
        self.destination = None
        self.target_id = None
        self.attacking = False
        self.message = "Choose a highlighted tile."

    def feed(self):
        if self.selected:
            return self.commit(self.planned_position(), "feed")
        return False

    def preview(self):
        if self.target_id:
            low, high, hp_low, hp_high = self.sim.attack_preview(self.selected, self.target_id, self.planned_position())
            return f"Damage {low}-{high}. Target HP after: {hp_low}-{hp_high}. A/Enter confirms."
        if self.destination is not None:
            return "Stepped. Choose Attack, Feed, Wait, or Cancel."
        return ""

    def click(self, point):
        sim = self.sim
        if not sim.human_turn or point is None:
            return
        if self.destination is not None and self._popup_choice(point):
            return
        tile = self.renderer.camera.tile_at(point) if self.renderer else (int(point[1] // TILE_SIZE), int(point[0] // TILE_SIZE))
        if tile is None or not sim.grid.in_bounds(tile):
            return
        if self.attacking:
            target = next((a for a in self.targets() if a.pos == tile), None)
            if target:
                self.target_id = target.agent_id
                self.message = "A or Attack confirms the strike. Esc cancels."
            return
        own = next((a for a in sim.predators + sim.prey
                    if a.alive and a.pos == tile and a.side == sim.player_side), None)
        if own:
            self.reset()
            self.selected = own.agent_id if own.agent_id in sim.pending_player_ids else None
            self.message = "Choose a destination, or act from this tile." if self.selected else "That animal has already acted."
        elif self.selected:
            if tile in sim.observe(self.selected).legal_destinations:
                self.destination = tile
                self.target_id = None
                self.attacking = False
                self.message = "Stepped. Choose a command."
            else:
                self.message = "Choose a highlighted destination."

    def commit(self, tile, kind="wait", target_id=None):
        try:
            self.sim.submit_player_action(self.selected, Action(tile, kind=kind, target_id=target_id))
        except ValueError as error:
            self.message = str(error)
            return False
        self.reset()
        self.message = "Command resolved. Select another animal or end turn."
        return True

    def _options(self):
        sim = self.sim
        options = []
        if self.targets():
            options.append(("attack", "Attack"))
        if (sim.player_side == "prey" and getattr(sim, "kind", "") != "skirmish"
                and sim.grid.resources_remaining.get(self.planned_position(), 0)):
            options.append(("feed", "Feed"))
        options.append(("wait", "Wait"))
        options.append(("cancel", "Cancel"))
        return options

    def _popup_rects(self):
        if self.destination is None or self.renderer is None:
            return []
        camera = self.renderer.camera
        row, col = self.destination
        origin_x, origin_y = camera.origin()
        left = origin_x - camera.x + (col + 1) * camera.tile_size + 8
        top = origin_y - camera.y + row * camera.tile_size
        width, height, gap = 132, 32, 4
        options = self._options()
        if left + width > camera.width:
            left = origin_x - camera.x + col * camera.tile_size - width - 8
        top = max(8, min(top, camera.height - (len(options) * (height + gap))))
        return [
            (pygame.Rect(left, top + index * (height + gap), width, height), name, label)
            for index, (name, label) in enumerate(options)
        ]

    def _popup_choice(self, point):
        if point is None:
            return False
        for rect, name, _label in self._popup_rects():
            if not rect.collidepoint(point):
                continue
            if name == "attack":
                self.attack()
            elif name == "feed":
                self.feed()
            elif name == "wait":
                self.wait()
            else:
                self.cancel()
            return True
        return False

    def wait(self):
        if self.selected and self.sim.human_turn:
            return self.commit(self.planned_position())
        return False

    def draw(self, canvas, renderer):
        sim = self.sim
        if not sim.player_side:
            return
        destination_canvas = canvas
        canvas = pygame.Surface((sim.grid.width*TILE_SIZE, sim.grid.height*TILE_SIZE), pygame.SRCALPHA)
        def outline(pos, color, width=2, inset=2):
            r, c = pos
            pygame.draw.rect(canvas, color, (c*TILE_SIZE+inset, r*TILE_SIZE+inset,
                             TILE_SIZE-2*inset, TILE_SIZE-2*inset), width)
        for pred in sim.predators:
            if pred.alive and pred.can_attack():
                for pos in sim.grid.passable_neighbors(pred.pos):
                    r, c = pos
                    pygame.draw.circle(canvas, (232, 84, 42, 180),
                                       (c * TILE_SIZE + TILE_SIZE - 5, r * TILE_SIZE + 5), 3)
        if sim.human_turn:
            for agent in sim.predators + sim.prey:
                if agent.alive and agent.agent_id in sim.pending_player_ids:
                    x, y = agent.pos[1]*TILE_SIZE, agent.pos[0]*TILE_SIZE
                    pygame.draw.circle(canvas, (246, 248, 240, 230), (x + 6, y + 6), 4)
            if self.selected in sim.pending_player_ids:
                observation = sim.observe(self.selected)
                shade = pygame.Surface((TILE_SIZE-2,TILE_SIZE-2), pygame.SRCALPHA)
                shade.fill((246, 248, 240, 70))
                for pos in observation.legal_destinations:
                    if pos != observation.actor.pos:
                        canvas.blit(shade, (pos[1]*TILE_SIZE+1,pos[0]*TILE_SIZE+1))
                        outline(pos, (246, 248, 240, 220), 2, 2)
                x, y = observation.actor.pos[1]*TILE_SIZE, observation.actor.pos[0]*TILE_SIZE
                pygame.draw.rect(canvas, (20, 36, 28, 230),
                                 (x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4), 2)
                if self.destination is not None:
                    outline(self.destination, (232, 84, 42, 255), 3)
                    actor = next(unit for unit in sim.predators + sim.prey if unit.agent_id == self.selected)
                    sprite = renderer.assets.get_sprite(actor.species, TILE_SIZE, include_label=False)
                    canvas.blit(sprite, (self.destination[1] * TILE_SIZE, self.destination[0] * TILE_SIZE))
                    if self.destination != actor.pos:
                        veil = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        veil.fill((18, 36, 26, 150))
                        canvas.blit(veil, (actor.pos[1] * TILE_SIZE, actor.pos[0] * TILE_SIZE))
                if self.attacking:
                    for target in self.targets():
                        outline(target.pos, (232, 84, 42, 255), 3)
        renderer.blit_map(destination_canvas, canvas)
        for rect, _name, label in self._popup_rects():
            card(destination_canvas, rect, PAPER, radius=12)
            renderer.queue_text(label, INK, rect.center, size=15, bold=True, centered=True)
