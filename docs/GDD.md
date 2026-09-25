# Predator & Prey — Game Design Document (v1.0, locked)

## 1. Overview
Predator & Prey is a strategic, grid-based game supporting PvE (watch the
AI run) and PvP. Predators hunt to eliminate prey; prey herds race to
consume a majority of the map's resources before being wiped out.

**Scope for this project**: exactly two sides (Predator vs Prey) per
match. No FFA / 3rd-side modes in v1.

## 2. Turn Structure
Alternating full-team turns: Predators act completely (move + attack for
every unit), then Prey act completely (move + feed for every unit).
Predators act first each round.

## 3. Map
- 20×20 grid, river bisecting the map horizontally at row 10.
- Two 2-tile chokepoints crossing the river (natural ambush points).
- 3 feeding-ground clusters (tall grass, radius 2) and 3 discrete resource
  nodes.
- Rocks block line of sight and movement.

## 4. Units

| Unit | Side | HP | Damage | Kill rule | Move | Special |
|---|---|---|---|---|---|---|
| Tiger | Predator | — | one-shot | any prey, 1 hit | 1 tile | Solitary, no cooldown, no pack |
| Wolf | Predator | — | 60 | 1-shots Deer/Buffalo; 2 hits on Giraffe | 1 tile | Per-wolf cooldown after a kill |
| Deer | Prey | 40 | — | dies to 1 Tiger or 1 Wolf hit | 1 tile | Largest population |
| Buffalo | Prey | 60 | — | dies to 1 Tiger or 1 Wolf hit | 1 (2 over water) | Vulnerable at water mid-tile |
| Giraffe | Prey | 100 | — | 1 Tiger hit, or 2 Wolf hits (wounds persist) | 1 tile | Recovers +10 HP/turn feeding safely |

## 5. Locked Design Decisions
These were open questions in the v0.1 draft. Resolved for v1 build:

1. **Kill trigger = Zone of Control.** A predator threatens its own tile
   and all 8 adjacent tiles. A prey unit entering or crossing any
   threatened tile can be attacked that turn.
2. **Giraffe wounds persist across turns.** A Wolf can land one hit this
   turn and finish the Giraffe on a later turn (same or different Wolf).
3. **Wolf cooldown is per-wolf, not pack-wide.** Other wolves in the same
   pack can still attack on the same turn a packmate is on cooldown.
4. **Line of sight defaults to full awareness** in v1. LoS-limited mode
   (rocks block, tall grass conceals past 3 tiles) is implemented as a
   config toggle for a later mode, not the default.
5. **Buffalo's 2-tile water move is vulnerable at the mid-tile.** Any
   predator adjacent to the intermediate tile can still attack.
6. **Predator win condition**: 70% of the starting prey population
   eliminated.
7. **Prey win condition**: 65% of the map's starting aggregate resource
   pool consumed (tracked as one pool, not per-node).
8. **Giraffe recovery rate**: +10 HP per turn of uncontested feeding
   (same rate/action as ordinary resource progress).

## 6. AI Systems (see docs/ALGORITHMS.md for full spec)
- **Prey**: flock-shared pathing to the nearest resource (BFS), with two
  override states — PANIC (a predator was spotted) and DESPAIR (a
  flock-mate was attacked) — each driven by a rank-scored "fcost"
  function rather than raw distance.
- **Predator**: one intent rolled per match (Chase / Ambush / Camp),
  species-biased (Tiger → Camp, Wolf → Ambush). Wolves additionally
  coordinate as a pack: the closest wolf to prey sets the target tile,
  the furthest wolf executes the move, and no move may strand a
  packmate 3+ tiles behind.

## 7. Build Phasing (recommended)
Given the full scope (A*, FSM, FoV, influence maps, hotseat multiplayer,
particles, debug overlay, analytics) is a finished game, not a first
build, phase it:

1. **Core loop** — grid, agents, BFS/A* movement, combat, win/loss.
   Colored-square rendering only. *(This is what's scaffolded in this repo.)*
2. **AI layer** — full panic/despair fcost system, predator intents,
   pack coordination.
3. **Polish** — sprites, particles, floating combat text, debug overlay.
4. **Analytics** — CSV turn logging, Matplotlib population graphs.

The influence-map (scent/danger) system from the original tech spec is
deferred/likely-cut — it's largely redundant with the explicit
panic/despair AI already covering "danger awareness."

## 8. Glossary
- **Chokepoint** — one of the two river crossings; a natural ambush zone.
- **Zone of Control** — the tiles a unit threatens (its own + adjacent)
  for attack-trigger purposes.
- **Cooldown (Wolf)** — one-turn restriction on attacking again after a
  kill; movement is still allowed.
- **Feeding Ground** — tall-grass tiles where prey feed and Giraffe heals.
- **Resource Node** — a consumable point counting toward the prey win
  condition.
