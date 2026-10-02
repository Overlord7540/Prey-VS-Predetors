"""
Entry point. Loads config, spawns a default scenario, and runs the
Pygame loop (Input -> Update -> Draw) per the tech spec's execution flow.

Run with:  python -m src.main

Controls:
    SPACE       pause / resume
    + / -       speed up / slow down
    T           toggle detailed / fast playback
    N           pause and advance one action (or round in fast mode)
    R           restart with a new random scenario
    G / H       tile grid / terrain guide
    M           home menu
    Esc         leave the match for the previous page (cancels a plan first)
    W / E       wait / end player turn
    A / F       attack (confirm with A/Enter) / feed
    Z / arrows  tile size / pan camera
    C / ESC     focus selected unit / cancel planned command
    F1          toggle debug overlay (predator intents, prey states)
"""
from __future__ import annotations

import argparse
import pygame

from src.ai.catalog import PLAYER_LABELS, wildlife_catalog

DIFFICULTY_LABELS = {"baseline": "Calm", "tactical": "Wary", "learned": "Sharp",
                     "rules": "Calm", "search": "Wary"}
from src.application.classical_training import train_table_players
from src.rendering.player import PlayerView
from src.rendering.menu import CLEARINGS, DUELS, menu_buttons, draw_menu
from src.rendering.controls import game_buttons, draw_buttons, button_enabled
from src.core.scenario import build_default_scenario
from src.data.loader import sized_scenario
from src.rendering.asset_manager import AssetManager
from src.rendering.skirmish import SkirmishMatch
from src.rendering.renderer import Renderer, TILE_SIZE
from src.rendering.viewport import fit_viewport, initial_window_size, window_to_canvas

STEP_EVERY_MS_BASE = 900  # one simulation turn every N ms at 1x speed
SPEED_STEPS = [0.25, 0.5, 1.0, 2.0, 4.0]
DEFAULT_SPEED_INDEX = 2  # 1.0x


def main() -> None:
    parser = argparse.ArgumentParser(description="Predator & Prey simulation")
    parser.add_argument("--seed", type=int, help="Reproducible match; R repeats this seed")
    parser.add_argument("--scenario", choices=("riverlands", "basin"), default="riverlands",
                        help="riverlands is deer only; basin adds a buffalo herd")
    parser.add_argument("--board", choices=("small", "large"), default="large",
                        help="large is 20×20, with a 12×12 skirmish; small is 12×10")
    parser.add_argument("--mode", choices=("watch", "predator", "prey"), help="Skip the mode menu")
    parser.add_argument("--controller", choices=wildlife_catalog().playable_names(), default="tactical")
    args = parser.parse_args()

    start_name = "noon"

    def open_match(player_side):
        match = build_default_scenario(
            seed=args.seed, scenario_name=sized_scenario(clearing, large_board),
            start=start_name)
        opponent = wildlife_catalog().create(opponent_name)
        if player_side == "predator":
            match.controllers["prey"] = opponent
        elif player_side == "prey":
            match.controllers["predator"] = opponent
        else:
            match.default_controller = opponent
        match.opponent_label = DIFFICULTY_LABELS.get(opponent_name, PLAYER_LABELS.get(opponent_name, opponent_name))
        return match

    def battle_name():
        kind = DUELS[renderer.duel_index % len(DUELS)][0]
        stem = "skirmish" if kind == "ford" else kind
        return f"{stem}_large" if large_board else stem

    pygame.init()
    opponent_name = args.controller
    clearing = args.scenario
    skirmish_name = "rules"
    skirmish_player = None
    large_board = args.board == "large"
    mode = args.mode
    return_page = "home"
    sim = open_match(mode if mode in ("predator", "prey") else None)
    assets = AssetManager()
    renderer = Renderer(sim, assets)
    renderer.menu_page = "title" if mode is None else "home"
    renderer.menu_focus = 0
    renderer.large_board = large_board
    sim.player_side = mode if mode in ("predator", "prey") else None
    player = PlayerView(sim, renderer)

    canvas = pygame.Surface(renderer.screen_size())
    desktop_size = pygame.display.get_desktop_sizes()[0]
    screen = pygame.display.set_mode(
        initial_window_size(canvas.get_size(), desktop_size), pygame.RESIZABLE)

    pygame.display.set_caption("Prey vs Predators")
    clock = pygame.time.Clock()

    speed_index = DEFAULT_SPEED_INDEX
    paused = False
    detailed = True
    time_since_step = 0
    running = True
    menu_keyboard = False
    last_focus = None

    while running:
        dt = clock.tick(60)
        buttons = menu_buttons(canvas.get_size(), renderer.menu_page) if mode is None else game_buttons(renderer, detailed, paused)

        for event in pygame.event.get():
            if event.type == pygame.MOUSEMOTION:
                menu_keyboard = False
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(
                    (max(1, event.w), max(1, event.h)), pygame.RESIZABLE)
            renderer.handle_debug_toggle(event)
            buttons = menu_buttons(canvas.get_size(), renderer.menu_page) if mode is None else game_buttons(renderer,detailed,paused)

            command = event.key if event.type == pygame.KEYDOWN else None
            clicked_command = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                canvas_pos = window_to_canvas(event.pos, canvas.get_size(), screen.get_size())
                hit_ui = mode is not None and renderer.show_help and canvas_pos is not None and renderer.help_rect().collidepoint(canvas_pos)
                for rect, key, label in ([] if hit_ui else buttons):
                    if canvas_pos is not None and rect.collidepoint(canvas_pos):
                        hit_ui = True
                        if mode is None or button_enabled(key, sim, player):
                            command = key
                            clicked_command = True
                if not hit_ui and mode is not None:
                    player.click(canvas_pos)
                    if sim.events:
                        renderer.capture_events()
                        sim.events.clear()
            if command == pygame.K_m:
                mode = None
                renderer.menu_page = "home"
                renderer.menu_focus = 0
                continue
            if mode is not None and command == pygame.K_ESCAPE:
                planning = player.attacking or player.destination is not None or player.target_id is not None
                if clicked_command or not planning:
                    mode = None
                    renderer.menu_page = return_page
                    renderer.menu_focus = 0
                    continue
            if mode is None:
                if command in (pygame.K_UP, pygame.K_DOWN):
                    menu_keyboard = True
                    renderer.menu_focus = (renderer.menu_focus + (1 if command == pygame.K_DOWN else -1)) % len(buttons)
                    continue
                if command == pygame.K_RETURN:
                    command = buttons[renderer.menu_focus][1]
                if command == pygame.K_ESCAPE:
                    if renderer.menu_page == "title":
                        running = False
                    elif renderer.menu_page == "home":
                        renderer.menu_page = "title"
                    elif renderer.menu_page == "sides":
                        renderer.menu_page = "face"
                    elif renderer.menu_page == "battle_face":
                        renderer.menu_page = "skirmish"
                    elif renderer.menu_page == "classical":
                        renderer.menu_page = "face"
                    elif renderer.menu_page == "face":
                        renderer.menu_page = "clearing"
                    elif renderer.menu_page == "clearing":
                        renderer.menu_page = "play"
                    elif renderer.menu_page == "skirmish":
                        renderer.menu_page = "duel"
                    elif renderer.menu_page == "duel":
                        renderer.menu_page = "play"
                    elif renderer.menu_page == "play":
                        renderer.menu_page = "home"
                    else:
                        renderer.menu_page = "home"
                    renderer.menu_focus = 1 if renderer.menu_page == "duel" else 0
                    continue
                if renderer.menu_page == "title":
                    if command in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_1):
                        renderer.menu_page = "home"
                        renderer.menu_focus = 0
                    continue
                if renderer.menu_page == "settings":
                    if command == pygame.K_z:
                        renderer.camera.zoom()
                    elif command == pygame.K_g:
                        renderer.show_grid = not renderer.show_grid
                    elif command == pygame.K_t:
                        detailed = not detailed
                    elif command == pygame.K_b:
                        large_board = not large_board
                        renderer.large_board = large_board
                    continue
                if renderer.menu_page == "face":
                    if command in (pygame.K_1, pygame.K_2, pygame.K_3):
                        opponent_name = {pygame.K_1: "baseline", pygame.K_2: "tactical", pygame.K_3: "learned"}[command]
                        renderer.menu_page = "sides"
                        renderer.menu_focus = 0
                    elif command == pygame.K_4:
                        renderer.menu_page = "classical"
                        renderer.menu_focus = 0
                    continue
                if renderer.menu_page == "classical":
                    names = {
                        pygame.K_1: "logistic", pygame.K_2: "tree", pygame.K_3: "forest",
                        pygame.K_4: "bayes", pygame.K_5: "markov",
                    }
                    if command in names:
                        opponent_name = names[command]
                        renderer.menu_page = "sides"
                        renderer.menu_focus = 0
                    continue
                if renderer.menu_page == "training":
                    if command == pygame.K_1:
                        train_table_players(matches=2, max_rounds=8, seed=1)
                    continue
                if renderer.menu_page == "play":
                    if command == pygame.K_1:
                        renderer.menu_page = "clearing"
                        renderer.menu_focus = 0
                    elif command == pygame.K_2:
                        renderer.menu_page = "duel"
                        renderer.menu_focus = 1
                    continue
                if renderer.menu_page == "duel":
                    index = renderer.duel_index % len(DUELS)
                    if command in (pygame.K_LEFT, pygame.K_RIGHT):
                        step = 1 if command == pygame.K_RIGHT else -1
                        renderer.duel_index = (index + step) % len(DUELS)
                        renderer.menu_focus = 1
                        continue
                    names = {pygame.K_1: "field", pygame.K_2: "ford", pygame.K_3: "stone"}
                    if command in names:
                        renderer.duel_index = [item[0] for item in DUELS].index(names[command])
                        command = pygame.K_RETURN
                    if command == pygame.K_RETURN:
                        renderer.menu_page = "skirmish"
                        renderer.menu_focus = 0
                    continue
                if renderer.menu_page == "clearing":
                    index = getattr(renderer, "clearing_index", 0) % len(CLEARINGS)
                    if command in (pygame.K_LEFT, pygame.K_RIGHT):
                        step = 1 if command == pygame.K_RIGHT else -1
                        renderer.clearing_index = (index + step) % len(CLEARINGS)
                        renderer.menu_focus = 1
                        continue
                    starts = {pygame.K_7: "dawn", pygame.K_8: "noon", pygame.K_9: "dusk"}
                    if command in starts:
                        renderer.start_name = start_name = starts[command]
                        renderer.menu_focus = {pygame.K_7: 3, pygame.K_8: 4, pygame.K_9: 5}[command]
                        continue
                    names = {getattr(pygame, f"K_{slot + 1}"): item[0] for slot, item in enumerate(CLEARINGS)}
                    if command in names:
                        clearing = names[command]
                        renderer.clearing_index = [item[0] for item in CLEARINGS].index(clearing)
                        renderer.menu_page = "face"
                        renderer.menu_focus = 0
                    elif command == pygame.K_RETURN:
                        clearing = CLEARINGS[index][0]
                        renderer.menu_page = "face"
                        renderer.menu_focus = 0
                    continue
                if renderer.menu_page == "skirmish":
                    if command in (pygame.K_1, pygame.K_2, pygame.K_3):
                        skirmish_name = {pygame.K_1: "rules", pygame.K_2: "search", pygame.K_3: "learned"}[command]
                        skirmish_player = None
                        return_page = "skirmish"
                        mode = "skirmish"
                        sim = SkirmishMatch(skirmish_name, args.seed, battle_name=battle_name())
                        sim.opponent_label = DIFFICULTY_LABELS[skirmish_name]
                        tile_size, show_grid = renderer.camera.tile_size, renderer.show_grid
                        clearing_index, start_name = renderer.clearing_index, renderer.start_name
                        duel_index = renderer.duel_index
                        renderer = Renderer(sim, assets)
                        renderer.labels = {piece.agent_id: piece.battle_name for piece in sim.predators + sim.prey}
                        renderer.camera.tile_size, renderer.show_grid = tile_size, show_grid
                        renderer.large_board = large_board
                        renderer.clearing_index, renderer.start_name = clearing_index, start_name
                        renderer.duel_index = duel_index
                        renderer.menu_page, renderer.menu_focus = "home", 0
                        player = PlayerView(sim, renderer)
                        paused = False
                        time_since_step = 0
                    elif command in (pygame.K_4, pygame.K_5):
                        skirmish_player = "hunter" if command == pygame.K_4 else "herd"
                        renderer.menu_page = "battle_face"
                        renderer.menu_focus = 0
                    continue
                if renderer.menu_page == "battle_face":
                    if command in (pygame.K_1, pygame.K_2, pygame.K_3):
                        skirmish_name = {pygame.K_1: "rules", pygame.K_2: "search", pygame.K_3: "learned"}[command]
                        return_page = "battle_face"
                        mode = "skirmish"
                        sim = SkirmishMatch(skirmish_name, args.seed, skirmish_player, battle_name())
                        sim.opponent_label = DIFFICULTY_LABELS[skirmish_name]
                        tile_size, show_grid = renderer.camera.tile_size, renderer.show_grid
                        clearing_index, start_name = renderer.clearing_index, renderer.start_name
                        duel_index = renderer.duel_index
                        renderer = Renderer(sim, assets)
                        renderer.labels = {piece.agent_id: piece.battle_name for piece in sim.predators + sim.prey}
                        renderer.camera.tile_size, renderer.show_grid = tile_size, show_grid
                        renderer.large_board = large_board
                        renderer.clearing_index, renderer.start_name = clearing_index, start_name
                        renderer.duel_index = duel_index
                        renderer.menu_page, renderer.menu_focus = "home", 0
                        player = PlayerView(sim, renderer)
                        if sim.human_turn:
                            player.selected = next(iter(sim.pending_player_ids))
                            player.message = "Choose a highlighted tile. A attacks, W waits."
                        paused = False
                        time_since_step = 0
                    continue
                if renderer.menu_page == "home":
                    if command == pygame.K_1:
                        renderer.menu_page = "play"
                        renderer.menu_focus = 0
                    elif command == pygame.K_2:
                        renderer.menu_page = "training"
                        renderer.menu_focus = 0
                    elif command == pygame.K_3:
                        renderer.menu_page = "settings"
                        renderer.menu_focus = 0
                    continue
                if renderer.menu_page == "sides" and command in (pygame.K_1, pygame.K_2, pygame.K_3):
                    return_page = "sides"
                    mode = {pygame.K_1: "predator", pygame.K_2: "prey", pygame.K_3: "watch"}[command]
                    side = None if mode == "watch" else mode
                    sim = open_match(side)
                    sim.player_side = side
                    tile_size, show_grid = renderer.camera.tile_size, renderer.show_grid
                    clearing_index, start_name = renderer.clearing_index, renderer.start_name
                    duel_index = renderer.duel_index
                    renderer = Renderer(sim, assets)
                    renderer.camera.tile_size, renderer.show_grid = tile_size, show_grid
                    renderer.large_board = large_board
                    renderer.clearing_index, renderer.start_name = clearing_index, start_name
                    renderer.duel_index = duel_index
                    renderer.menu_page, renderer.menu_focus = "home", 0
                    player = PlayerView(sim, renderer)
                    paused = False
                    time_since_step = 0
                continue
            if command is not None:
                if command == pygame.K_e and sim.human_turn and getattr(sim, "kind", "") != "skirmish":
                    sim.end_player_turn()
                    renderer.capture_events()
                    sim.events.clear()
                    player.reset()
                    paused = False
                    time_since_step = 0
                elif command == pygame.K_w and player.wait():
                    renderer.capture_events()
                    sim.events.clear()
                elif command in (pygame.K_a, pygame.K_RETURN) and sim.human_turn:
                    if player.attack():
                        renderer.capture_events()
                        sim.events.clear()
                elif command == pygame.K_f and sim.human_turn:
                    if player.feed():
                        renderer.capture_events()
                        sim.events.clear()
                elif command == pygame.K_ESCAPE:
                    player.reset()
                    player.message = "Plan cancelled. Select an animal."
                elif command == pygame.K_z:
                    renderer.camera.zoom()
                elif command == pygame.K_c:
                    actor_id = player.selected or sim.active_agent_id
                    actor = next((a for a in sim.predators+sim.prey if a.agent_id == actor_id), None)
                    if actor:
                        renderer.camera.focus(actor.pos)
                elif command == pygame.K_h:
                    renderer.show_help = not renderer.show_help
                elif command == pygame.K_g:
                    renderer.show_grid = not renderer.show_grid
                elif command == pygame.K_t:
                    detailed = not detailed
                    time_since_step = 0
                elif command == pygame.K_n:
                    paused = True
                    time_since_step = 0
                    if not sim.is_over() and not sim.human_turn:
                        renderer.effects.clear()
                        sim.step_action() if detailed else sim.step()
                        renderer.capture_events()
                        sim.events.clear()
                elif command == pygame.K_SPACE:
                    paused = not paused
                elif command in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    speed_index = min(speed_index + 1, len(SPEED_STEPS) - 1)
                elif command in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    speed_index = max(speed_index - 1, 0)
                elif command == pygame.K_r:
                    tile_size, show_grid = renderer.camera.tile_size, renderer.show_grid
                    clearing_index, start_name = renderer.clearing_index, renderer.start_name
                    duel_index = renderer.duel_index
                    if mode == "skirmish":
                        sim = SkirmishMatch(skirmish_name, args.seed, skirmish_player, battle_name())
                        sim.opponent_label = DIFFICULTY_LABELS[skirmish_name]
                    else:
                        side = None if mode == "watch" else mode
                        sim = open_match(side)
                        sim.player_side = side
                    renderer = Renderer(sim, assets)
                    if mode == "skirmish":
                        renderer.labels = {piece.agent_id: piece.battle_name for piece in sim.predators + sim.prey}
                    renderer.camera.tile_size, renderer.show_grid = tile_size, show_grid
                    renderer.large_board = large_board
                    renderer.clearing_index, renderer.start_name = clearing_index, start_name
                    renderer.duel_index = duel_index
                    renderer.menu_page, renderer.menu_focus = "home", 0
                    player = PlayerView(sim, renderer)
                    if getattr(sim, "kind", "") == "skirmish" and sim.human_turn:
                        player.selected = next(iter(sim.pending_player_ids))
                        player.message = "Choose a highlighted tile. A attacks, W waits."
                    time_since_step = 0
                    paused = False

        if mode is not None:
            keys = pygame.key.get_pressed()
            renderer.camera.pan(round((keys[pygame.K_RIGHT]-keys[pygame.K_LEFT])*dt*.6),
                                round((keys[pygame.K_DOWN]-keys[pygame.K_UP])*dt*.6))
        if renderer.hit_stop <= 0 and not paused:
            time_since_step += dt

        step_interval = STEP_EVERY_MS_BASE / SPEED_STEPS[speed_index]
        if (renderer.hit_stop <= 0 and mode is not None and not paused and not sim.human_turn
                and not sim.is_over() and time_since_step >= step_interval):
            sim.step_action() if detailed else sim.step()
            renderer.capture_events()
            sim.events.clear()
            time_since_step = 0
        if getattr(sim, "kind", "") == "skirmish" and sim.human_turn and player.selected not in sim.pending_player_ids:
            player.reset()
            player.selected = next(iter(sim.pending_player_ids))
            player.message = "Choose a highlighted tile. A attacks, W waits."

        renderer.update(0.0 if paused else dt / 1000.0)
        focus_key = (sim.turn, sim.phase, sim.active_agent_id)
        if mode is not None and focus_key != last_focus:
            if sim.human_turn:
                actor = next((a for a in sim.predators+sim.prey if a.agent_id in sim.pending_player_ids), None)
            else:
                actor = next((a for a in sim.predators+sim.prey if detailed and a.agent_id == sim.active_agent_id), None)
            if actor:
                renderer.camera.glance(actor.pos)
            last_focus = focus_key
        renderer.detailed = detailed
        renderer.selected_agent_id = player.selected
        renderer.playback_speed = SPEED_STEPS[speed_index]
        renderer.player_message = player.message
        renderer.command_preview = player.preview()
        renderer.attack_confirmation = player.target_id is not None
        logical_mouse = window_to_canvas(pygame.mouse.get_pos(), canvas.get_size(), screen.get_size())
        renderer.hovered_tile = None
        if logical_mouse is not None:
            renderer.hovered_tile = renderer.camera.tile_at(logical_mouse)
        if mode is None:
            buttons = menu_buttons(canvas.get_size(), renderer.menu_page)
            renderer.menu_focus %= len(buttons)
            if not menu_keyboard and logical_mouse:
                for i, (rect, _, _) in enumerate(buttons):
                    if rect.collidepoint(logical_mouse):
                        renderer.menu_focus = i
            draw_menu(canvas, renderer, None if menu_keyboard else logical_mouse)
        else:
            renderer.draw(canvas)
            player.draw(canvas, renderer)
            # Rebuild after input: label/enabled state and click regions stay in sync.
            buttons = game_buttons(renderer, detailed, paused)
            draw_buttons(canvas, renderer, player, buttons, logical_mouse)
            renderer.draw_help(canvas)

        viewport = pygame.Rect(fit_viewport(canvas.get_size(), screen.get_size()))
        screen.fill((18, 36, 26))
        if viewport.size == canvas.get_size():
            screen.blit(canvas, viewport.topleft)
        else:
            screen.blit(pygame.transform.scale(canvas, viewport.size), viewport.topleft)
        renderer.draw_text(screen, viewport)
        if mode is not None and pygame.mouse.get_focused():
            renderer.draw_hover(screen, viewport, pygame.mouse.get_pos())
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
