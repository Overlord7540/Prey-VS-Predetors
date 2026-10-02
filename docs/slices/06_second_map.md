# Slice 6 — second map and buffalo

Requirements: phase-1 blueprint slice 6. Two maps. Four roles in a match: tiger, wolf, deer, and buffalo. Buffalo water movement stays out.

## Design

The riverlands layout stays `config/map.json` and `config/scenario.json`. The basin is `config/maps/basin.json` plus `config/scenarios/basin.json`.

A scenario may name `"map"`. `build_default_scenario` loads that file. Omitting it still loads `config/map.json`, so current tests keep the riverlands board.

The basin is the same tile vocabulary and the same win rules, with a different geography: the river is higher, there is one ford, and rocks leave a gap in the south pasture. Buffalo spawn there. They use the existing prey controller. Their stats already set the role: 60 HP, move 3, food yield 2. Giraffe healing is not wired.

`python -m src.main --scenario basin` starts that match. The default remains riverlands.
