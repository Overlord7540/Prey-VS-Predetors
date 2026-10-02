# Slice 12 — rule-based skirmish

Requirements: step the roster from `docs/slices/11_battle_roster.md`. Move, then attack or wait. Wildlife matches keep their own rules.

## Design

`BattleMatch` activates hunters in roster order, then the herd. One step is one fighter. A destination must be reachable in move range and visible from the current tile. A blow is legal only from the tile the fighter ends on, against an adjacent enemy that tile can see. Rivers and rocks still block. A chokepoint tile reduces that blow by 4, to a minimum of 1. Wiping out a side ends the fight.

`RuleBattleController` takes a legal blow against the weakest enemy it can reach. Otherwise it steps toward the far side of the board. It does not search future turns. The wildlife catalog is unchanged.
