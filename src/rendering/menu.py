"""Title screen: the habitat fills the window, and the choices sit in the middle."""
from __future__ import annotations

import textwrap

import pygame

from src.application.classical_training import training_lines, verdict
from src.rendering.chrome import INK, MOSS, MUTED, PAPER, SIGNAL, card
from src.rendering.minimap import blit_duel, blit_preview

CLEARINGS = (
    ("glade", "Glade", "Open grass. Learn how far a step reaches."),
    ("rocks", "Rocks", "A stone wall. Learn what an animal cannot see."),
    ("ford", "Ford", "A river and a buffalo. Learn what crossing costs."),
    ("riverlands", "Riverlands", "The wide meadow. Deer, wolves, and a tiger."),
    ("basin", "Basin", "A buffalo herd and one giraffe."),
    ("rookery", "Rookery", "Hares, a heron, and a pair of jackals."),
)

DUELS = (
    ("field", "Field", "Open ground. Both packs start in sight."),
    ("ford", "Ford", "The river funnels the fight."),
    ("stone", "Stone", "Stone hides the other pack."),
)


def _rows(size, count):
    width, height = size
    row_width = min(560, width - 96)
    row_height, gap = (58, 8) if count >= 7 else (72, 14)
    stack = count * row_height + max(0, count - 1) * gap
    top = max(132, (height - stack) // 2)
    if top + stack + 72 > height:
        top = max(96, height - stack - 72)
    left = (width - row_width) // 2
    return [pygame.Rect(left, top + index * (row_height + gap), row_width, row_height)
            for index in range(count)]


def _choice_rects(size, page):
    choices = menu_choices(page)
    if page == "title":
        rect = pygame.Rect(0, 0, min(340, size[0] - 96), 72)
        rect.center = (size[0] // 2, int(size[1] * 0.70))
        return [rect]
    if page == "training":
        width, height = size
        row_width = min(560, width - 96)
        left = (width - row_width) // 2
        top = height - 72 * 2 - 14 - 64
        return [pygame.Rect(left, top + index * 86, row_width, 72) for index in range(2)]
    if page == "clearing":
        return _clearing_rects(size)
    if page == "duel":
        return _duel_rects(size)
    return _rows(size, len(choices))


def _clearing_rects(size):
    width, height = size
    center = pygame.Rect(0, 0, min(520, width - 520), min(380, height - 300))
    center.midtop = (width // 2, 108)
    side = pygame.Rect(0, 0, min(220, center.x - 36), min(300, center.height - 40))
    left = side.copy()
    left.centery = center.centery
    left.right = center.left - 24
    right = side.copy()
    right.centery = center.centery
    right.left = center.right + 24
    chip_w, chip_h, gap = 112, 44, 10
    row = chip_w * 3 + gap * 2
    chip_y = center.bottom + 12
    chips = [pygame.Rect(center.centerx - row // 2 + index * (chip_w + gap), chip_y, chip_w, chip_h)
             for index in range(3)]
    back = pygame.Rect(0, 0, 280, 52)
    back.centerx = width // 2
    back.top = chip_y + chip_h + 12
    return [left, center, right, *chips, back]


def _duel_rects(size):
    width, height = size
    center = pygame.Rect(0, 0, min(520, width - 520), min(420, height - 240))
    center.midtop = (width // 2, 120)
    side = pygame.Rect(0, 0, min(220, center.x - 36), min(300, center.height - 40))
    left = side.copy()
    left.centery = center.centery
    left.right = center.left - 24
    right = side.copy()
    right.centery = center.centery
    right.left = center.right + 24
    back = pygame.Rect(0, 0, 280, 52)
    back.centerx = width // 2
    back.top = center.bottom + 16
    return [left, center, right, back]


def menu_buttons(size, page="sides"):
    """Expose the same rectangles that are painted as menu choices."""
    choices = menu_choices(page)
    return [(rect, key, label) for rect, (key, label) in zip(_choice_rects(size, page), choices)]


def menu_choices(page):
    back = (pygame.K_ESCAPE, "Back")
    if page == "title":
        return [(pygame.K_RETURN, "Enter game")]
    if page == "home":
        return [(pygame.K_1, "New game"), (pygame.K_2, "Field notes"), (pygame.K_3, "Settings"), back]
    if page == "play":
        return [(pygame.K_1, "Meadow"), (pygame.K_2, "Duel"), back]
    if page == "duel":
        return [(pygame.K_LEFT, "Previous"), (pygame.K_RETURN, "This ground"),
                (pygame.K_RIGHT, "Next"), back]
    if page == "clearing":
        return [(pygame.K_LEFT, "Previous"), (pygame.K_RETURN, "This clearing"),
                (pygame.K_RIGHT, "Next"), (pygame.K_7, "Dawn"), (pygame.K_8, "Noon"),
                (pygame.K_9, "Dusk"), back]
    if page == "face":
        return [(pygame.K_1, "Calm"), (pygame.K_2, "Wary"), (pygame.K_3, "Sharp"),
                (pygame.K_4, "Study the careful mind"), back]
    if page == "settings":
        return [(pygame.K_z, "Tile size [Z]"), (pygame.K_g, "Grid [G]"), (pygame.K_t, "Playback [T]"),
                (pygame.K_b, "Board [B]"), back]
    if page == "skirmish":
        return [
            (pygame.K_1, "Calm"), (pygame.K_2, "Wary"), (pygame.K_3, "Sharp"),
            (pygame.K_4, "Play the tiger pack"), (pygame.K_5, "Play the jackals"), back,
        ]
    if page == "classical":
        return [
            (pygame.K_1, "Logistic regression"), (pygame.K_2, "Decision tree"),
            (pygame.K_3, "Random forest"), (pygame.K_4, "Naive Bayes"),
            (pygame.K_5, "Markov model"), back,
        ]
    if page == "training":
        return [(pygame.K_1, "Train table players"), back]
    if page == "battle_face":
        return [(pygame.K_1, "Calm"), (pygame.K_2, "Wary"), (pygame.K_3, "Sharp"), back]
    return [(pygame.K_1, "Play predators"), (pygame.K_2, "Play prey"), (pygame.K_3, "Watch AI"), back]


def _paint_field(canvas, assets):
    tile = 32
    width, height = canvas.get_size()
    for y in range(0, height, tile):
        for x in range(0, width, tile):
            canvas.blit(assets.get_tile("open_field", tile, variant=(x // tile + y // tile) % 4), (x, y))


def _draw_landing_title(canvas, renderer):
    """A meadow title: green prey, red predators, vines, and claw marks."""
    width, height = canvas.get_size()
    prey = (118, 164, 118)
    versus = (236, 230, 210)
    predators = (196, 88, 84)
    vine = (58, 108, 72)
    claw = (214, 78, 68)
    font = pygame.font.SysFont("georgia", 64, bold=True)
    words = [("PREY", prey), ("VS", versus), ("PREDATORS", predators)]
    gap = 22
    rendered = [font.render(word, True, color) for word, color in words]
    total = sum(item.get_width() for item in rendered) + gap * (len(rendered) - 1)
    x = (width - total) // 2
    y = int(height * 0.34)
    for surface, (word, color) in zip(rendered, words):
        renderer.queue_text(word, color, (x, y), size=64, bold=True)
        x += surface.get_width() + gap
    title_left = (width - total) // 2
    title_right = title_left + total
    pygame.draw.lines(canvas, vine, False, [
        (title_left - 88, y + 52), (title_left - 54, y + 24),
        (title_left - 28, y + 42), (title_left - 10, y + 18),
    ], 4)
    pygame.draw.circle(canvas, vine, (title_left - 64, y + 28), 5)
    pygame.draw.circle(canvas, vine, (title_left - 22, y + 30), 4)
    pygame.draw.lines(canvas, vine, False, [
        (title_right + 108, y + 48), (title_right + 82, y + 22),
        (title_right + 58, y + 40),
    ], 4)
    pygame.draw.circle(canvas, vine, (title_right + 90, y + 26), 4)
    for step in range(3):
        pygame.draw.line(canvas, claw, (title_right + 36 + step * 12, y + 8),
                         (title_right + 60 + step * 12, y + 52), 4)


def _draw_clearing_carousel(canvas, renderer, rows, mouse_pos):
    """Three boards in a row. Left and right move through the clearings."""
    left, center, right, *chips, back = rows
    index = getattr(renderer, "clearing_index", 0) % len(CLEARINGS)
    large = getattr(renderer, "large_board", False)
    start = getattr(renderer, "start_name", "noon")
    hovered = next((slot for slot, rect in enumerate(rows)
                    if mouse_pos is not None and rect.collidepoint(mouse_pos)), None)
    selected = hovered if hovered is not None else getattr(renderer, "menu_focus", 1) % len(rows)
    renderer.queue_text("Prey vs Predators", PAPER, (left.x, 28), size=36, bold=True)
    renderer.queue_text("Move left and right. The board in the middle is the one you will play.",
                        PAPER, (left.x, 72), size=16)
    windows = (
        (left, (index - 1) % len(CLEARINGS), False),
        (center, index, True),
        (right, (index + 1) % len(CLEARINGS), False),
    )
    for slot, (rect, clearing_index, current) in enumerate(windows):
        name, title, blurb = CLEARINGS[clearing_index]
        fill, color = (INK, PAPER) if slot == selected else (PAPER, INK)
        card(canvas, rect, fill, radius=22)
        map_box = pygame.Rect(rect.x + 16, rect.y + 16, rect.width - 32, rect.height - (88 if current else 48))
        painted = blit_preview(canvas, map_box, name, large, renderer.assets, start)
        if not current:
            shade = pygame.Surface(painted.size, pygame.SRCALPHA)
            shade.fill((18, 36, 26, 90))
            canvas.blit(shade, painted.topleft)
            chevron = "<" if slot == 0 else ">"
            renderer.queue_text(chevron, color, (rect.centerx, rect.bottom - 28), size=22, bold=True, centered=True)
        else:
            renderer.queue_text(title, color, (rect.x + 20, rect.bottom - 62), size=22, bold=True)
            renderer.queue_text(blurb, MUTED if slot != selected else PAPER,
                                (rect.x + 20, rect.bottom - 34), size=14)
            renderer.queue_text(f"{index + 1} / {len(CLEARINGS)}", color,
                                (rect.right - 48, rect.bottom - 62), size=14)
    for slot, (rect, label) in enumerate(zip(chips, ("Dawn", "Noon", "Dusk")), start=3):
        active = label.lower() == start
        if slot == selected:
            fill, color = SIGNAL, PAPER
        elif active:
            fill, color = INK, PAPER
        else:
            fill, color = PAPER, INK
        card(canvas, rect, fill, radius=14)
        renderer.queue_text(label, color, (rect.centerx, rect.centery), size=16, bold=active, centered=True)
    back_fill, back_color = (INK, PAPER) if selected == 6 else (PAPER, INK)
    card(canvas, back, back_fill, radius=18)
    renderer.queue_text("Back", back_color, (back.centerx, back.centery), size=20, bold=True, centered=True)
    renderer.queue_text("Left and right change the clearing. 7, 8, and 9 change where the animals start.",
                        PAPER, (left.x, canvas.get_height() - 36), size=14)


def _draw_duel_carousel(canvas, renderer, rows, mouse_pos):
    """Three duel boards. The center card is the ground the packs will fight on."""
    left, center, right, back = rows
    index = getattr(renderer, "duel_index", 1) % len(DUELS)
    large = getattr(renderer, "large_board", False)
    hovered = next((slot for slot, rect in enumerate(rows)
                    if mouse_pos is not None and rect.collidepoint(mouse_pos)), None)
    selected = hovered if hovered is not None else getattr(renderer, "menu_focus", 1) % len(rows)
    renderer.queue_text("Prey vs Predators", PAPER, (left.x, 28), size=36, bold=True)
    renderer.queue_text("Two packs. The board in the middle is the one you will play.",
                        PAPER, (left.x, 72), size=16)
    windows = (
        (left, (index - 1) % len(DUELS), False),
        (center, index, True),
        (right, (index + 1) % len(DUELS), False),
    )
    for slot, (rect, duel_index, current) in enumerate(windows):
        name, title, blurb = DUELS[duel_index]
        fill, color = (INK, PAPER) if slot == selected else (PAPER, INK)
        card(canvas, rect, fill, radius=22)
        map_box = pygame.Rect(rect.x + 16, rect.y + 16, rect.width - 32, rect.height - (88 if current else 48))
        painted = blit_duel(canvas, map_box, name, large, renderer.assets)
        if not current:
            shade = pygame.Surface(painted.size, pygame.SRCALPHA)
            shade.fill((18, 36, 26, 90))
            canvas.blit(shade, painted.topleft)
            chevron = "<" if slot == 0 else ">"
            renderer.queue_text(chevron, color, (rect.centerx, rect.bottom - 28), size=22, bold=True, centered=True)
        else:
            renderer.queue_text(title, color, (rect.x + 20, rect.bottom - 62), size=22, bold=True)
            renderer.queue_text(blurb, MUTED if slot != selected else PAPER,
                                (rect.x + 20, rect.bottom - 34), size=14)
            renderer.queue_text(f"{index + 1} / {len(DUELS)}", color,
                                (rect.right - 48, rect.bottom - 62), size=14)
    back_fill, back_color = (INK, PAPER) if selected == 3 else (PAPER, INK)
    card(canvas, back, back_fill, radius=18)
    renderer.queue_text("Back", back_color, (back.centerx, back.centery), size=20, bold=True, centered=True)
    renderer.queue_text("Left and right change the ground. 1, 2, and 3 jump to Field, Ford, and Stone.",
                        PAPER, (left.x, canvas.get_height() - 36), size=14)


def draw_menu(canvas, renderer, mouse_pos=None):
    """Draw the habitat, a title, and the choice bands for this page."""
    renderer.text_items.clear()
    renderer.map_text_count = 0
    width, height = canvas.get_size()
    page = getattr(renderer, "menu_page", "sides")
    choices = menu_choices(page)
    rows = _choice_rects(canvas.get_size(), page)
    _paint_field(canvas, renderer.assets)
    shade = pygame.Surface((width, height), pygame.SRCALPHA)
    shade.fill((18, 36, 26, 88))
    canvas.blit(shade, (0, 0))

    if page == "clearing":
        _draw_clearing_carousel(canvas, renderer, rows, mouse_pos)
        return
    if page == "duel":
        _draw_duel_carousel(canvas, renderer, rows, mouse_pos)
        return
    if page == "title":
        _draw_landing_title(canvas, renderer)
    elif page == "training":
        renderer.queue_text("Prey vs Predators", PAPER, (96, 28), size=36, bold=True)
        renderer.queue_text("Field notes", PAPER, (96, 72), size=16)
        report = []
        for line in training_lines():
            report.extend(textwrap.wrap(line, width=100) or [""])
        for index, line in enumerate(report[:20]):
            renderer.queue_text(line, PAPER, (96, 100 + index * 20), size=15)
    else:
        renderer.queue_text("Prey vs Predators", PAPER, (rows[0].x, rows[0].y - 78), size=40, bold=True)
        subtitle = {
            "home": "Start a match, or open the notes.",
            "play": "A meadow, or a fight between two packs.",
            "face": "How hard the other side thinks.",
            "sides": "Choose your side.",
            "settings": "Adjust the view.",
            "skirmish": "Watch the duel, or take a pack.",
            "battle_face": "How hard the other side thinks.",
            "classical": "Students of the careful mind.",
        }.get(page, "Choose how this match is played.")
        renderer.queue_text(subtitle, PAPER, (rows[0].x, rows[0].y - 32), size=16)

    hovered = next((index for index, rect in enumerate(rows)
                    if mouse_pos is not None and rect.collidepoint(mouse_pos)), None)
    selected = hovered if hovered is not None else getattr(renderer, "menu_focus", 0) % len(choices)
    labels = [label for _, label in choices]
    if page == "settings":
        labels[:3] = [
            f"Tiles: {renderer.camera.tile_size}px [Z]",
            f"Grid: {'On' if renderer.show_grid else 'Off'} [G]",
            f"Playback: {'Detailed' if renderer.detailed else 'Fast'} [T]",
        ]
        labels[3] = f"Board: {'Large' if getattr(renderer, 'large_board', False) else 'Small'} [B]"
    portraits = ("tiger", "deer", "wolf")
    if page == "home":
        portraits = ("tiger", "wolf", "deer", "buffalo", "tiger")
    elif page == "skirmish":
        portraits = ("tiger", "wolf", "jackal", "tiger", "jackal")
    elif page == "battle_face":
        portraits = ("wolf", "tiger", "deer")
    for index, (rect, label) in enumerate(zip(rows, labels)):
        if index == selected and hovered is not None:
            fill, color = SIGNAL, PAPER
        elif index == selected:
            fill, color = INK, PAPER
        else:
            fill, color = PAPER, INK
        card(canvas, rect, fill, radius=20)
        if page == "title":
            renderer.queue_text(label, color, (rect.centerx, rect.centery), size=22, bold=True, centered=True)
            continue
        renderer.queue_text(label, color, (rect.x + 28, rect.y + 22), size=22)
        renderer.queue_text(pygame.key.name(choices[index][0]), MOSS if index != selected else PAPER,
                            (rect.right - 28, rect.centery), size=16, bold=True, centered=True)
        if index == selected and choices[index][0] != pygame.K_ESCAPE:
            sprite = renderer.assets.get_sprite(portraits[index % len(portraits)], 48, include_label=False)
            canvas.blit(sprite, sprite.get_rect(midright=(rect.right - 56, rect.centery)))

    rules = renderer.sim.grid.rules
    descriptions = (
        ("Command the predators.",
         f"Eliminate {rules.predator_win_prey_elimination_pct:.0%} of the herd."),
        ("Command the prey.",
         f"Gather {rules.prey_win_resource_pool_pct:.0%} of the food."),
        ("Observe an AI match.", "Detailed or fast playback."),
        ("Return to the previous page.", ""),
    )
    if page == "home":
        descriptions = (
            ("Pick a meadow or a duel.", ""),
            ("How each mind was trained.", "The charts and the five students live here."),
            ("Adjust your view and playback.", "Settings apply to the next match."),
            ("Return to the title.", ""),
        )
    elif page == "play":
        descriptions = (
            ("Herd and hunters on the grass.", ""),
            ("Tiger pack against jackals.", ""),
            ("Return to the main menu.", ""),
        )
    elif page == "skirmish":
        descriptions = (
            ("Both sides take the nearest blow.", "This is the Calm mind."),
            ("Both sides look one reply ahead.", "This is the Wary mind."),
            ("Both sides use the battle network.", "This is the Sharp mind."),
            ("You command Sable, Ash, and Birch.", "Then choose how hard the jackals think."),
            ("You command Cinder, Nettle, and Bramble.", "Then choose how hard the tiger pack thinks."),
            ("Return to the previous page.", ""),
        )
    elif page == "battle_face":
        descriptions = (
            ("The other side takes the nearest blow.", ""),
            ("The other side looks one reply ahead.", ""),
            ("The other side uses the battle network.", ""),
            ("Return to the duel.", ""),
        )
    elif page == "face":
        descriptions = (
            ("Walks toward the nearest prize.", "This is the Greedy mind."),
            ("Watches the herd and the danger.", "This is the Tactical mind."),
            ("Learned by playing whole matches.", "This is the neural policy."),
            ("Five students that copied Tactical.", "Open Field notes to see if they improved."),
            ("Return to the previous page.", ""),
        )
    elif page == "classical":
        descriptions = (
            ("Scores each tile with a weighted sum.", verdict("logistic")),
            ("A few yes-or-no questions about the tile.", verdict("tree")),
            ("Five trees vote on the tile.", verdict("forest")),
            ("Each feature votes on its own.", verdict("bayes")),
            ("The next step depends on the last one.", verdict("markov")),
            ("Return to the meadow.", ""),
        )
    elif page == "training":
        descriptions = (("", ""), ("", ""))
    elif page == "settings":
        descriptions = (
            ("32 shows the whole large board. 64 and 96 are closer.", "Arrow keys pan when the board is bigger than the view."),
            ("Show or hide tile borders.", ""),
            ("Watch individual actions or full rounds.", ""),
            ("Large is the starting board: 20×20, and a 12×12 skirmish.", "Small is 12×10. The next match uses this board."),
            ("Return to the main menu.", ""),
        )
    elif page == "title":
        descriptions = (("", ""),)
    for index, line in enumerate(descriptions[selected]):
        if line:
            renderer.queue_text(line, PAPER, (rows[0].x, rows[-1].bottom + 28 + index * 24), size=16)
    hint = "Enter starts the game. Esc quits." if page == "title" else "Arrows select. Enter confirms. Esc goes back."
    renderer.queue_text(hint, PAPER, (rows[0].x, height - 36), size=14)
