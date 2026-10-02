# Slice 2 — folder boundaries

Requirements: `docs/PHASE1_BLUEPRINT.md` slice 2. No gameplay rule changes.

## Design

New work enters through these objects. Existing match code stays in place so play does not move in this slice.

| Object | Module | Job |
|--------|--------|-----|
| `ControllerCatalog` | `src/ai/catalog.py` | Names the wildlife controllers. Creates only playable ones. |
| `RuleBasedController` | `src/ai/baselines` (re-export) | Greedy / finite-state baseline. Class still defined in `src/ai/policies.py`. |
| `TacticalController` | `src/ai/tactical` (re-export) | Hand-written utility policy. Same definition as today. |
| `LearnedController` | `src/ai/learned/controller.py` | Future trained policy. Not playable until weights exist. |
| `BatchEvaluation` | `src/application/evaluation.py` | Runs seeded matches and returns a result record. No files, no charts. |
| `ResultStore` | `src/adapters/persistence/result_store.py` | Saves and loads that record as JSON. |
| `ComparisonChartReport` | `src/adapters/reports/charts.py` | Draws win-rate and training-curve figures. The only module that imports matplotlib. |
| `PygameUI` | `src/adapters/pygame_ui/boundary.py` | Loads display types on demand. Importing the module does not import pygame. |

`src/core` and `src/ai` do not import pygame or matplotlib. `src/rendering` remains the current display code. The art slice may move those modules; until then, new UI code asks `PygameUI` instead of reaching into rendering from application or AI packages.

`python -m src.experiments.run` stays the command. It calls `BatchEvaluation` and `ResultStore`. The JSON record shape is unchanged.
