# Slice 10 — one battle, rules only

Requirements: phase 2, step 1. One fight. No campaign, no chapters, no supports. Wildlife rules stay as they are. This note does not add battle code.

## What a turn is

Two sides alternate. On a side's turn, each living fighter activates once, in roster order, so a seed replays.

One activation is move, then act:

1. Move to a passable tile within move range, or stay. A straight step costs 1. A diagonal step costs 2. Rivers and rocks block. Corners stay blocked.
2. Act: attack one enemy in range, or wait. One attack per activation. Moving through a tile does not start a fight.

Attack range is 1 (adjacent, eight directions). Damage uses the same seeded spread as the wildlife stats for that body. No food, panic, adrenaline, or feeding.

## Win

Eliminate the other side. A round cap can end the match unfinished. There is no seize tile.

## Terrain

The battle reuses the wildlife tiles. Open ground is empty. Rivers and rocks block movement and sight. A fighter standing on a chokepoint tile takes 4 less damage, to a minimum of 1. Feeding grounds and resource nodes are ordinary ground in a battle.

## Roster

Three against three. Names sit on the existing bodies so the battle can reuse the current sprites.

| Name | Body | Side | HP | Move | Damage |
|------|------|------|----|------|--------|
| Sable | tiger | hunter | 48 | 3 | 32 ± 10 |
| Ash | wolf | hunter | 36 | 4 | 22 ± 6 |
| Birch | wolf | hunter | 36 | 4 | 22 ± 6 |
| Fern | deer | herd | 40 | 5 | 16 ± 4 |
| Moss | deer | herd | 40 | 5 | 16 ± 4 |
| Boulder | buffalo | herd | 60 | 3 | 18 ± 4 |

Herd fighters can attack. Hunters are not the only side that deals damage.

## Sight

Sight range stays 6. Rocks block sight. A fighter may move and attack only using tiles and enemies it can see. Search and the later battle network use that same limit.

## What comes after this note

1. One small battle map and this roster, as data. Wildlife scenarios keep loading as they do now.
2. A rule-based battle controller, then a shallow search opponent.
3. A second network, trained on battle observations. It does not load `config/policies/wildlife.json`.
4. The same experiment shape: rules vs search vs learned, with saved charts.

Menu, art, and juice for the battle wait until that match can be stepped in tests.
