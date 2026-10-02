# Phase 1 blueprint

Status: slice 1 of `PROJECT_DIRECTION.md`. This is the requirements and gap list for the wildlife sim. It does not change rules. Phase 2 (one character battle) stays out of this document.

Gameplay rules that already exist stay authoritative in `GDD.md`. This file says what phase 1 keeps, what it adds, and when a slice is done.

## Keep

These stay the wildlife rules unless a later slice’s design note says otherwise:

- One round is predators, then prey, then a victory check.
- Each unit activates once: a legal move, then Attack, Feed, or Wait.
- Eight-direction movement, occupancy, blocked diagonal corners.
- Explicit adjacent attacks. No walk-by reaction attacks. Seeded damage.
- Food depletes and does not regrow. Predators win at about 70% prey removed. Prey win at about 65% food eaten.
- Fear states NORMAL, PANIC, DESPAIR stay simulation rules, not a replacement for the player’s command.
- Headless `Simulation`, swappable controllers, seeded matches, `python -m src.experiments.run`.
- Human play and watch mode stay. Rendering does not decide legality.

Default cast on riverlands: 1 tiger, 2 wolves, deer herds. The basin scenario adds a buffalo herd on a second map. Giraffe healing and buffalo water movement are not in play.

## Already in code, not yet the phase-1 product

| Piece | Where | Gap |
|-------|--------|-----|
| Tactical utility policy | `src/ai/policies.py`, `src/ai/tactics.py` | Compared with baseline and learned in `results/figures/`. |
| Learned policy | `src/ai/learned/`, `config/policies/wildlife.json` | Trained offline. Loaded by `--controller learned`. |
| Greedy / FSM baseline | `src/ai/fsm.py` | Same. |
| FoV helpers | `src/ai/fov.py` | Not applied to observations. |
| Influence map | `src/ai/influence_map.py` | Stub. Not used by a policy or drawn. |
| Batch runner | `src/experiments/run.py` | Writes a result file. No chart adapter. |
| Pixel drawing | `src/rendering/pixel_art.py` | Not a locked palette and silhouette set. |
| Maps | `config/map.json`, `config/maps/basin.json` | Two layouts. Basin is selected with `--scenario basin`. |
| Roles | `config/units.json`, `config/scenarios/basin.json` | Tiger, wolf, deer, and buffalo are in the basin match. Giraffe is still unused. |

## Add before phase 1 is done

**AI.** Observations respect field of view. The tactical policy uses influence and path costs. Wolves keep coordinated approach. A trainer fits a small neural policy (or equivalent reinforcement learner) on those same limited observations and exposes it as a controller object.

**Proof.** One experiment compares greedy, tactical, and learned on shared seeds. Saved figures show win rate, the training curve, prey remaining, and food consumed. Matplotlib stays in a reports adapter.

**Content.** Two maps. Four roles in play: tiger, wolf, deer, and buffalo as the slow high-HP prey. Giraffe healing and buffalo water movement stay optional stretch goals, not required for phase 1.

**Presentation.** Sprites, tiles, and UI art are PNG files under `assets/`. The renderer loads and scales them by whole numbers. It does not draw animals with code. Map-first UI, legal-move and threat readability, then juice that does not change the simulation.

**Structure.** Only the boundaries needed for controllers, training, assets, and reports. Core does not import pygame or matplotlib.

## Four roles

| Role | Side | Phase-1 job |
|------|------|-------------|
| Tiger | Predator | Short move, high damage, solitary hunt |
| Wolf | Predator | Longer move, pack approach tiles |
| Deer | Prey | Fast forager, panic and herd goals |
| Buffalo | Prey | Slower, higher HP, higher food yield |

A fifth animal waits until one of those four has stats, an AI hook, and a sprite family.

## Slice order

Same sequence as the plan. Slice 1 is this file.

1. This blueprint
2. Folder boundaries for controllers, training, assets, and reports
3. Field of view on observations; influence in the tactical policy and the debug overlay
4. Pixel pipeline, approved at game size, then the rest of the cast
5. Clear play, then juice
6. Second map and buffalo in a scenario
7. Train the wildlife network and load it as a controller
8. Result records and phase-1 charts
9. Demo seed that can show the learned side and the figures

Each remaining slice needs a short design note, tests, and a review before the next one starts. Slices that change AI also need charts once the reports adapter exists. Until slice 8, AI slices still save structured numbers so charts can be generated later without rerunning by hand.

## Done means

Phase 1 is done when all of these are true:

- A person can play or watch a wildlife match on two maps with tiger, wolf, deer, and buffalo.
- Agents do not act on tiles outside their field of view.
- Greedy, tactical, and learned controllers run through the same experiment entry point.
- `results/figures/` contains the comparison and training charts.
- Core tests pass without pygame.
- Phase 2 has not been started.

## Not in phase 1

Character battle, minimax, a second neural net, campaign UI, weapon systems, and a map editor.
