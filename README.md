# Predator & Prey

A turn-based tactical AI prototype in Python. The simulation runs without
Pygame; play either side against the rule-based AI, or watch detailed unit actions
and fast full rounds.

## Run

From this project directory (not the outer workspace):

```powershell
python -m pip install -r requirements.txt
python -m src.main
python -m src.main --seed 42
python -m pytest tests/ -v
```

The outer workspace main.py is an older standalone prototype.
With --seed, restarting repeats that match. Without it, R creates a fresh match.

## Play against AI

Start with `python -m src.main`, then choose Play predators, Play prey, or Watch AI.
Use `--mode predator`, `--mode prey`, or `--mode watch` to skip the menu.

On your turn, select an animal and a highlighted destination. This stages a move;
it does not spend the action until you choose Attack [A], Feed [F], or Wait [W].
For an attack, click a highlighted enemy to preview damage and remaining HP,
then press A/Enter (or Attack again) to confirm. Esc cancels the plan.
W moves to the planned destination without attacking or feeding. E ends the
side's turn; all unused units wait without automatically attacking or feeding.

Movement budgets: tiger 3, wolf 4, deer 5, buffalo 3, giraffe 4. A straight step
costs 1 and a diagonal step costs 2. Occupied cells and blocked diagonal corners
are excluded. A buffalo can step onto river tiles (up to 2 in one move) and is
easier to hit if it stops in the channel. A giraffe regains 10 health, up to its
maximum, at the start of its activation.
Tiger damage is a seeded integer roll from 22–42; wolf damage is 16–28.
A surviving prey gains +2 movement and protection from further hits until its
next activation completes, followed by two activations without another boost.
Automatic movement-triggered attacks have been removed.
Fear states remain visible but never replace your movement command.
Red outlines show current ready predator attack zones, not predicted future moves.
Predators win by eliminating 70% of starting prey; prey win by consuming 65% of
starting food. Both thresholds round up to whole units. Progress is in the sidebar.
M returns to the main menu, and R restarts the chosen mode.
Fast playback always stops for human input. The opponent uses the controller from
`--controller` (default `tactical`). `learned` loads the trained weights. Hover over an
animal for its last decision explanation.

## Controls and display

- T or Mode button: Detailed / Fast. Fast processes one round per 900 ms at 1x.
- SPACE or Pause button: pause/resume.
- N or Next button: advance one action/phase, or one round in Fast, then pause.
- +/-: speed from 0.25x to 4x. R: restart. F1: debug overlay. G: tile grid. H: terrain guide.
- Z: switch 48px/64px tiles. Arrow keys: pan. C: focus selected/active unit.
- Main menu: Play, Simulation, Settings, Quit. Arrows/Enter navigate; Esc goes back.
- Resize/maximize the window; text renders at native window resolution.
- Individual labels D1, D2, W1, W2, T1 remain stable after deaths.
- Hover over a living animal for identity, health/state, intent and attack status.
- KILL/HIT effects and recent events identify combat. Food stock pips and brown
  EMPTY tiles show depletion. Pause freezes effects; restart clears them.

## Tactical presentation

The revised animals use 32x32 source sprites with finer silhouettes and shading.
Terrain uses a quieter palette so units and move highlights remain distinct.
The map takes most of the screen height. A restrained navy-and-ivory panel groups
turn status, objectives, selected-unit details, and commands. Wait and End Turn
are separate from playback and navigation. The title screen uses a short choice
list and one map vignette; hover a choice to see its objective.

G toggles the tile grid. H opens/closes the terrain guide. Terrain details appear
when hovering the map, and unit tooltips retain AI decision explanations. Unit
identity badges stay visible; health is shown in the unit panel to avoid covering
sprites. UI text renders at the final window resolution; artwork uses nearest-
neighbor scaling. The map camera pans across the full board instead of shrinking its tiles to fit.

Presentation is split across rendering/pixel_art.py, asset_manager.py, menu.py,
controls.py, renderer.py and player.py. Rendering does not change simulation rules.

## Repeatable experiments

```powershell
python -m src.experiments.train
python -m src.experiments.compare --seed 0 --matches 4 --max-rounds 40
python -m src.main --seed 7 --controller learned
```

`compare` writes `results/comparison.json` and the figures in `results/figures/`.
The demo seed is `config/demo.json`.

```powershell
python -m src.experiments.run --seed 0 --matches 100 --max-rounds 300 --output results.json
```

This runs without Pygame and records each seed, outcome, rounds, surviving prey,
food consumed, and the configuration. A round limit reports unfinished matches
rather than inventing a winner. Keep code revision and results together when
comparing changes. Each simulation owns its random generator.

Compare the retained baseline with the new default using
`python -m src.experiments.run --controller baseline --matches 10` and
`python -m src.experiments.run --controller tactical --matches 10`.

## Project structure

- src/core/: live state, validated rules, turn scheduling, perception/state
  transitions, combat, controller contract, and structured records.
- src/ai/: pure movement decisions, pathfinding, and RuleBasedController.
- src/rendering/: graphics, responsive viewport, text, labels, captions, effects.
- src/data/: configuration loading.
- src/experiments/: headless seeded evaluations.
- config/: map/behavior rules, species stats, terrain, and starting scenario.
- tests/: regression tests, public controller/seed tests, and shared builders.

Read docs/GDD.md for the authoritative current gameplay rules,
docs/ALGORITHMS.md for implemented AI, and docs/ARCHITECTURE.md for extension
points. The outer PDF and slides are historical and have not been updated.

## Current scope

Working: navigation, feeding, occupancy, fear states, combat, seeded scenarios,
controller injection, a trained wildlife policy, and comparison charts.
Not yet integrated: buffalo water movement, giraffe healing, or the phase-2 battle.

Verification is headless in the available environment. Pygame visual behavior
still needs checking on a machine with the graphics dependencies installed.
