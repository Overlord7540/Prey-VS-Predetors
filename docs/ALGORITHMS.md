# Implemented AI

## Decisions versus state

The default TacticalController and legacy RuleBasedController consume a detached Observation and returns an Action
(destination, action kind, optional target ID). It cannot mutate live state. The simulation prepares fear
states and shared goals through core/perception.py, validates movement, and
resolves attacks/feeding. Pathfinding and policy choices do not mutate their
inputs. All controllers currently receive full awareness, matching the existing
prototype; observations must be filtered before claiming limited perception.

## Default tactical policy

Prey score each legal move and waiting against all predators. Immediate adjacency
exposure costs 100 points per ready predator; predicted next-turn exposure costs
30. Multi-source BFS supplies distance to reachable stocked food (2 points per
step). Capped predator distance, escape-neighbor count and DESPAIR regrouping
break tradeoffs. Safe food underfoot is consumed before moving elsewhere.
Prediction checks the full legal predator movement range followed by adjacency, treating current
occupancy as fixed. It is a heuristic, not a guaranteed safety forecast; attack
damage and future prey movements are not modeled. PANIC/DESPAIR still update by
the same simulation rules, and increase the preference for predator distance.

Wolves sharing a pack_id cooperate; unassigned wolves form one implicit team.
A team chooses prey using summed shortest approach distances, then assigns
unique reachable adjacent attack tiles in stable wolf-ID order. Equal-length
routes prefer separation from assigned tiles. Assignments are recomputed from
live snapshots for each action; earlier moves can change later assignments.
Predators first select an explicit attack from reachable cells, preferring
lower-HP unprotected prey and shorter movement. Otherwise wolves coordinate
approaches and other predators hunt reachable target-adjacent cells. The legacy
baseline retains solo intents.

Actions include a short reason, recorded by agent ID and shown on hover. These
are descriptions of the policy decision, not claims of learning or reasoning
from a language model. No neural network or training algorithm is included.

## Baseline prey

BFS finds stocked resources. A* routes to a shared herd goal while excluding
occupied tiles. If that route is blocked, BFS finds another accessible resource.
Safe prey wait to eat stocked food underfoot. PANIC ranks legal neighboring
moves and waiting by distance from the predator plus proximity to food.
DESPAIR ranks distance from the predator plus proximity to the nearest living
flockmate unless already within two tiles. Higher combined rank wins. Ties
follow deterministic candidate order. There are up to nine candidates because
waiting is included. See GDD.md for detection, lockout and recovery rules.

## Baseline predators

At creation, a match-owned random generator selects CHASE, AMBUSH or CAMP,
with double weight for the configured intent_bias. Target selection uses the
closest living prey by Chebyshev distance; list order breaks ties.
CHASE uses A* toward a target-adjacent tile. AMBUSH approaches the midpoint of
the prey and its closest food. CAMP aims across the river and approaches prey
within three tiles. Unreachable derived targets can still cause waiting.
Adjacency attacks and cooldowns are simulation rules, not policy permissions.

## Deferred systems

step_predator_pack, the line-of-sight helpers, and influence_map are not wired
into default gameplay. In the legacy baseline a pack_id prevents solo movement. They are
not used by the new coordination policy in tactics.py. Neither controller has limited perception.

## Evaluation

Use src.experiments.run for repeatable batches. Compare controllers under the
same rules, initial seeds, round caps, and opponent policies. Report unfinished
matches. Evaluate generalization on held-out seeds/scenarios before making
claims about learned performance. No training algorithm is included yet.

Choose `--controller baseline` or `--controller tactical` in the batch runner.
The recorded controller name identifies the selected policy. A historical pre-tactical-combat 10-seed smoke
comparison (seeds 0–9, cap 150 rounds) yielded baseline 7 predator / 3 prey wins
and tactical 1 predator / 9 prey wins. Both sides changed together; this small
sample is not evidence of balanced play or isolated policy superiority.

After the movement/damage/escape update, seeds 0-7 (80-round cap) produced
8 predator wins with 40-50 food consumed. This preliminary sample indicates
predator-favored balance; it does not establish human-versus-AI difficulty.
