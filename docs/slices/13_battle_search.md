# Slice 13 — shallow skirmish search

Requirements: the search opponent from `docs/slices/10_battle_rules.md`. Two plies on the same legal moves as the rule controller. Wildlife catalog stays unchanged.

## Design

`SearchBattleController` scores every legal move and blow. The value is the expected damage of that blow, minus the strongest counter one visible enemy can land on the next activation. Damage uses the average of the seeded range. A chokepoint tile reduces the defender's rolls by 4 before the average. Hidden enemies are not in the view, so they are not in the search. If no enemy is visible, the search will not finish on a ford when any other legal tile exists.

The rule controller still takes the nearest weakest target. Search will leave that square when the counterattack is worse than striking from the ford.
