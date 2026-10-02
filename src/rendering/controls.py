"""Commands sit in a pad at the lower right. Playback sits under the board."""
import pygame

from src.rendering.chrome import INK, MOSS, PAPER, SIGNAL, card


def game_buttons(renderer, detailed, paused):
    _, height = renderer.screen_size()
    if renderer.sim.player_side and getattr(renderer.sim, "kind", "") == "skirmish":
        actions = []
    elif renderer.sim.player_side:
        actions = [(pygame.K_e, "End turn")]
    else:
        actions = [(pygame.K_n, "Next action" if detailed else "Next round")]
    utilities = [
        (pygame.K_ESCAPE, "Back"),
        (pygame.K_SPACE, "Resume" if paused else "Pause"),
        (pygame.K_t, "Detailed" if detailed else "Fast"),
        (pygame.K_m, "Menu"),
        (pygame.K_r, "Restart"),
    ]
    rail = renderer.unit_card_rect()
    gap = 8
    columns = 2 if len(actions) > 1 else 1
    rows = (len(actions) + columns - 1) // columns
    button_w = (rail.width - gap * (columns - 1)) // columns
    button_h = 48
    origin_x = rail.x
    origin_y = rail.bottom + 16
    buttons = []
    for index, (key, label) in enumerate(actions):
        column, row = index % columns, index // columns
        buttons.append((
            pygame.Rect(origin_x + column * (button_w + gap),
                        origin_y + row * (button_h + gap),
                        button_w, button_h),
            key, label,
        ))
    utility_w = 112
    utility_y = height - 20 - 42
    count = len(utilities)
    span = count * utility_w + (count - 1) * gap
    board_center = renderer.camera.origin()[0] + min(renderer.camera.width, renderer.sim.grid.width * renderer.camera.tile_size) // 2
    utility_x = max(20, board_center - span // 2)
    if utility_x + span > rail.x - 12:
        utility_x = 20
    for index, (key, label) in enumerate(utilities):
        buttons.append((
            pygame.Rect(utility_x + index * (utility_w + gap), utility_y, utility_w, 42),
            key, label,
        ))
    return buttons


def button_enabled(key, sim, player):
    if key in (pygame.K_a, pygame.K_f):
        if not sim.human_turn or player.selected not in sim.pending_player_ids:
            return False
        if key == pygame.K_a:
            return bool(player.targets())
        return sim.player_side == "prey" and bool(sim.grid.resources_remaining.get(player.planned_position(), 0))
    if key == pygame.K_e:
        return sim.human_turn and getattr(sim, "kind", "") != "skirmish"
    if key == pygame.K_w:
        return sim.human_turn and player.selected in sim.pending_player_ids
    if key == pygame.K_n:
        return not sim.human_turn and not sim.is_over()
    return True


def draw_buttons(canvas, renderer, player, buttons, mouse_pos):
    for rect, key, label in buttons:
        enabled = button_enabled(key, renderer.sim, player)
        hovered = enabled and mouse_pos is not None and rect.collidepoint(mouse_pos)
        primary = key in (pygame.K_e, pygame.K_a) and enabled and (
            key == pygame.K_e or renderer.attack_confirmation)
        if not enabled:
            fill, color = (214, 219, 206), (120, 128, 112)
        elif primary:
            fill, color = SIGNAL, PAPER
        elif hovered:
            fill, color = MOSS, PAPER
        else:
            fill, color = INK, PAPER
        card(canvas, rect, fill, radius=14)
        renderer.queue_text(label, color, rect.center, size=16, bold=primary, centered=True)
