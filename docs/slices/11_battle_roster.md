# Slice 11 — battle map and roster

Requirements: the data half of `docs/slices/10_battle_rules.md`. One 12 by 12 map and six named fighters. Wildlife scenarios still load herds. Nothing steps a battle yet.

## Design

`config/maps/skirmish.json` is a normal map file: a river on row 5, one ford on columns 5 and 6, and rocks that block sight. It has no feeding grounds and no resource nodes.

`config/battles/skirmish.json` lists Sable, Ash, Birch, Fern, Moss, and Boulder in roster order, with the stats from the rules note. `build_battle` checks the tiles and returns a `Battle`. It does not build a wildlife `Simulation`.

`load_named_scenario` only reads `config/scenarios/`. The name `skirmish` is not a wildlife match.
