# Current gameplay specification

This file supersedes the earlier prototype report and successive design notes.

## Match and turns

Two sides: predators and prey. A round consists of all predator actions, then
all surviving prey actions, victory evaluation, and one history record.
Detailed playback reveals phases and individual actions; Fast finishes the
same round. Each living unit gets one activation: a path-validated move followed
by Attack (predator), Feed (prey), or Wait. Human planning is cancellable until
the final action is committed. End Turn makes unused units wait.

Movement budgets in tiles: tiger 3, wolf 4, deer 5, buffalo 3, giraffe 4.
A straight step costs 1. A diagonal step costs 2. Impassable or occupied cells and
diagonals with either corner blocked cannot be crossed. No unit sharing or
teleportation is allowed. The UI and AI share the same legal destination set.
A buffalo may enter river tiles, up to its water budget of 2 per activation.
Stopping on a river tile adds 8 damage to the next hit. A giraffe regains 10
health at the start of its activation, capped at its maximum.

## Combat and escape

Attacks explicitly select one adjacent living prey, including diagonals. Each
predator gets at most one attack per round. Walking near a predator no longer
causes an automatic reaction attack. Humans see the raw damage range and the
possible remaining HP before confirming. Previewing never advances the RNG.

Damage is uniformly rolled from the simulation-owned seeded RNG: tiger 22–42,
wolf 16–28. Actual damage is capped at remaining HP. A wolf kill blocks attacks
for the entire next round but not movement. Wounds persist.

A surviving hit puts the herd into DESPAIR. If its adrenaline cooldown is zero,
the victim gets +2 movement and protection from further attacks until its next
activation completes. This guarantees an escape opportunity within side-based
turn ordering. The boost does not stack. The counter starts at three and drops
at the end of each prey activation: after the boosted activation, two further
activations must complete before another boost can trigger. Waiting consumes
the boost too. Predators cannot select protected prey as a valid target.

These are initial balance values. Pounce and pack-damage bonuses are not implemented.

## Food and terrain

Open field is walkable. Feeding ground is walkable with one food unit; a
resource node has two. Rivers and rocks block movement. Chokepoints are
walkable water crossings. Exhausted resources remain walkable, turn brown,
and do not regrow. Terrain concealment/line of sight is not active.
A Feed action consumes resource_yield at the final position; Wait does not.
AI auto commands retain automatic feeding for controller compatibility.
Giraffe healing and buffalo river crossing are active. Riverlands does not
spawn either animal; the basin match does.

## Fear and foraging

At the start of each prey phase, each unlocked herd selects its closest living
NORMAL member within panic_detection_range of a living predator. Ties prefer
shorter BFS distance to stocked food, then internal ID. That animal enters
PANIC. New panic entries are blocked for the next n full prey phases, where
n is registered herd membership. DESPAIR is not overwritten.
Before its action, PANIC recovers beyond panic_detection_range; DESPAIR recovers
beyond despair_recovery_range. No living predators also permits recovery.
Safe prey eat food underfoot. Normal prey share a resource goal until depletion;
if occupancy blocks it, they forage toward another reachable resource.

## Configuration and victory

config/map.json supplies dimensions, terrain placement, victory fractions,
and fear distances (default six and three). config/scenario.json supplies
predators and sampled herd spawn areas; default: one tiger, two independent
wolves, and three herds of two deer. config/units.json supplies active species
stats and intent bias. config/tiles.json supplies terrain properties.

Victory compares eliminated prey / starting prey against the predator threshold
(default 70%), then consumed food / starting food against the prey threshold
(default 65%). Predator victory takes precedence if both qualify at round end.
A zero denominator does not grant automatic victory. Earlier measured win rates
are historical and must be remeasured after changes to rules or AI.
