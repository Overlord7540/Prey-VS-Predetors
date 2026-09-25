# AI Algorithms Spec (cleaned up from original notes)

Implemented in `src/ai/pathfinding.py` and `src/ai/fsm.py`.

## Prey Movement — Normal State

- The initial path to a resource is the shortest route (BFS), and within
  a flock, whichever prey is closest to that resource "leads" — the
  whole flock adopts that prey's target and does not recompute a new
  path until the resource is depleted.
- If multiple prey are equidistant from *different* resources, one is
  picked at random to lead.
- Movement resolves sequentially within the flock, not simultaneously,
  but the target tile is always the one set by the closest-to-resource
  member regardless of move order.

## Prey — Panic State

**Trigger**: any flock member spots a predator. The closest prey to that
predator enters PANIC (tie-break: closer to a resource wins).

**Lockout**: once a prey enters PANIC, no other member of the flock may
enter PANIC for the next `n` turns, where `n` = number of animals in the
flock.

**Movement (fcost)**: for each of up to 8 adjacent tiles, compute two
rank-based scores (best candidate = 8, next = 7, ... not raw distance):
- Score A: how much this move increases distance from the predator.
- Score B: how much this move decreases distance to the nearest resource.

`fcost = Score A + Score B`. The move with the highest fcost is taken.

## Prey — Despair State

**Trigger**: any flock member is attacked, or is within 2 tiles of the
attacked member — the entire flock enters DESPAIR.

**Movement (fcost)**: only Score A (distance from predator) counts;
resource-seeking is dropped entirely. A second term is added: minimize
distance to the nearest flock-mate, *unless* that flock-mate is already
within 2 tiles (in which case this term is zero, to avoid needless
clumping).

## Predator — Target Selection

The closest living prey unit, recalculated every move (not sticky).

## Predator — Intent

Each predator rolls one intent at the start of the match, from
{Chase, Ambush, Camp}, used for its entire lifetime:
- Tiger is weighted toward **Camp**.
- Wolf is weighted toward **Ambush**.

- **Chase**: close the distance to the target using informed search (A*).
- **Ambush**: find the target's nearest resource, take the midpoint
  between the prey and that resource, and run Chase's algorithm toward
  that midpoint tile instead of the prey directly.
- **Camp**: sit in a hiding spot on the opposite side of the river from
  the target. If the target crosses the river and comes within 3 tiles,
  switch to Chase for the remainder of the approach.

**Kill trigger**: once a predator kills any prey, it permanently switches
to Chase for the rest of the match ("constant chase state").

## Predator — Pack Coordination (Wolves only)

- The pack's target tile is set by whichever wolf is closest to the prey.
- The wolf that actually **executes** a move is the one *furthest* from
  the prey (bringing stragglers up rather than piling the lead wolf in
  further).
- A candidate move is vetoed entirely if it would leave any pack member
  3+ tiles away from the pack's closest-to-prey wolf — packs don't
  outrun their own stragglers.
