# Predator & Prey — Tactical AI Simulation

A grid-based predator/prey ecosystem simulation and tactical strategy
game, built as an AI-lab class project. Prey navigate using flock-shared
BFS pathing with panic/despair fcost-scored fleeing; predators use A*
chase, ambush, and camp behaviors, including Wolf pack coordination.

## Status
**Phase 1 (core loop) is scaffolded and tested.** Grid, agents, BFS/A*
pathfinding, combat resolution, and win conditions all run headlessly
and pass automated tests. Rendering is wired to Pygame with color-fallback
"sprites" (no art assets needed to run it). Phases 2–4 (full AI polish,
visual/audio polish, analytics) are stubbed — see `docs/GDD.md` Section 7
for the build plan.

## Quick start
```bash
pip install -r requirements.txt
python -m src.main          # launch the playable/watchable prototype
pytest tests/ -v            # run the automated test suite
```

## Project layout
```
config/            Static data: units.json, tiles.json, map.json
src/core/          Grid, agents, combat, simulation loop — zero Pygame imports
src/ai/            Pathfinding (BFS/A*), fcost scoring, FSM/intents, FoV, influence map (stub)
src/rendering/     Pygame renderer, asset manager (color-fallback sprites), particles
src/data/          Config loader (JSON -> dataclasses)
src/main.py        Entry point: Input -> Update -> Draw loop
tests/             Pytest suite for pathfinding, combat, and simulation win-conditions
docs/GDD.md        Full game design doc, with previously-open questions now locked
docs/ALGORITHMS.md Cleaned-up spec for the prey/predator AI algorithms
```

## Design decisions
All previously-open design questions (kill-trigger rule, Giraffe wound
persistence, wolf cooldown scope, line-of-sight default, Buffalo water
vulnerability, win thresholds, grid layout) are locked in
`docs/GDD.md`, Section 5, and reflected directly in `config/*.json` and
`src/core/combat.py`.

## Tech stack
Python 3.11+, Pygame-ce (rendering), JSON (data config), Pytest (tests),
Matplotlib (planned for Phase 4 analytics — not yet wired in).
