# Slice 15 — skirmish charts

Requirements: the same experiment shape as wildlife, for rules, search, and the battle network. Figures come from the reports adapter.

## Design

`BattleEvaluation` plays every pair of different controllers on the same seeds, once with each side in the hunter seat. Self-play is not in this table. A win is counted for the controller that was on the winning side.

`python -m src.experiments.compare_battle` writes `results/battle_comparison.json` and three figures under `results/figures/`: `battle_wins.png`, `battle_health.png`, and `battle_training.png`. The wildlife figures are left in place.

The saved run is seeds 0–3, 8 rounds, measured after diagonal steps cost 2 and search stays off the ford until it sees an enemy. The network won 10 of 16, the rules 8 of 16, and search 6 of 16. All 16 games finished. That is a short sample, not a final ranking. The networks were not retrained for the new step cost.
