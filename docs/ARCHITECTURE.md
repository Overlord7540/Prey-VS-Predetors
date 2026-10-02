# Architecture and extension guide

## Responsibilities

- core/simulation.py orchestrates state changes, validates movement and resolves
  explicit commands and seeded combat. It has no Pygame or display wording dependency.
- core/turns.py schedules a single round, shared by both playback speeds.
- core/perception.py owns fear transitions and shared resource goals.
- core/rules.py defines validated immutable match rules.
- core/records.py contains events, round history, and structured action records.
- core/control.py defines Action, Observation and the Controller protocol.
- ai/policies.py implements the existing movement policy using fsm/pathfinding.
- rendering/identity.py formats display captions; renderer.py draws them.
- data/loader.py reads JSON. core/scenario.py constructs validated match state.

## Add a controller

Implement choose_action(observation) returning Action((row, column)). Returning
observation.actor.pos means wait. legal_destinations includes wait and currently
reachable cells within the species movement budget. The simulation independently validates against
live state: a controller cannot teleport or enter occupied/blocked tiles by
editing its snapshot. Malformed action types raise errors; well-formed illegal
moves become waiting. Legacy auto controller commands choose an adjacent attack target or feed; human Wait never does either.

Pass controllers to build_default_scenario(seed=42, controllers={...}). Keys
may be an individual agent_id or a side (predator/prey). Individual overrides
win over side overrides; TacticalController is the default. Observation
objects contain copied agents, grid, herd state, legal destinations and round
number. Nested data is mutable but detached, not deeply immutable. This favors
clarity over training throughput; a compact observation encoder can follow.

Action includes destination, kind (attack/feed/wait/auto), and target_id.
Observations include detached unit stats. Tactical policies use the same movement
budgets as humans. core/movement.py owns occupancy-aware path enumeration;
core/combat.py owns damage ranges and survivor effects. Simulation validates
human commands before movement or RNG consumption. rendering/player.py stages
cancellable plans and submits one final command. rendering/camera.py owns zoom,
pan and map hit testing without importing Pygame. Rewards and training adapters
remain future extensions.

## Reproducibility

build_default_scenario(seed=N) uses its own random.Random for setup and intent
and damage rolls; unrelated matches/global random calls cannot change it. Pass seed to
Simulation for direct construction. A stochastic custom controller should own
an explicitly seeded RNG too. Mid-round generator state is not a portable
checkpoint format. Keep evaluation outputs and code revisions together.

## Safe feature workflow

Specify the rule and observation/action impact first. Add configuration when
needed, implement domain rules separately from policy choices and display,
then verify public round/action behavior plus relevant focused unit tests.
Test fast/detailed equivalence, occupancy, and seeded reproducibility. Shared
builders live in tests/support.py. Some focused legacy tests intentionally
exercise private helpers; new integration tests should prefer public APIs.

This is a pragmatic modular prototype, not a claim of formal compliance with
an unspecified course SDC standard or a complete reinforcement-learning stack.

## Human turns

Simulation.player_side optionally reserves one side for human commands. The shared
round scheduler exposes human_turn and pending_player_ids; both stepping APIs stop
at that boundary. submit_player_action validates live legal destinations and spends
one action. end_player_turn resolves unused units as waits. Explicit actions enter
the same combat/feeding execution as AI actions, bypassing only policy selection.
PlayerView handles selection and overlays; the desktop loop handles mode selection
and input. Headless callers can use these APIs without importing Pygame.

## Tactical controller

TacticalController is the default; RuleBasedController remains the original
comparison policy. ai/tactics.py contains pure snapshot-based team assignment,
BFS distance fields and prey move scoring. Action.reason is optional, preserving
existing injected controllers. Simulation.decision_reasons stores the most recent
explanation per animal for inspection; player commands bypass AI choice as before.

## Pixel-art presentation

pixel_art.py contains original pixel sprites and deterministic terrain
textures. AssetManager caches nearest-neighbor-scaled surfaces, optionally loading
custom PNG animal overrides. Renderer uses 32-pixel board cells and native-resolution
text, with selected-animal information and objective progress in the sidebar.
menu.py owns the choice-list layout and hit rectangles. controls.py owns command layout
and enabled states, which main.py shares between drawing and input routing.
The same viewport mapping handles resizing for both menus and board interaction.

The tactical view groups turn commands with selection; playback and navigation
are separate. Reference terrain information is on demand (H), and hover shows
map details. Help removes underlying queued native text as well as painting its
panel, and blocks pointer activation of the commands it covers.
