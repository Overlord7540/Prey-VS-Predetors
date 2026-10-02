# Project Direction

This file is the **living plan**. When the plan changes, update the snapshot below and add a changelog entry. Do not keep a second competing plan elsewhere.

Status: **active plan** (agreed 2026-10-02). Slices 1–3 are done. Slice 4 has the first PNG set (grass, deer, tiger). Next art pass: the remaining animals and terrain.
Audience: future sessions working on this lab.
Course note: this is an AI course; AI-assisted design, coding, art pipelines, and evaluation are encouraged. Keep methods, results, and claims honest and reproducible.

Related docs: `GDD.md`, `ARCHITECTURE.md`, `ALGORITHMS.md`, `VISUAL_DIRECTION.md`. Those describe the code today. **This file wins** when they disagree about intended direction. Phase 1 extends the wildlife rules; phase 2 adds a separate battle rules note.

## Current plan snapshot

Two phases. Finish phase 1 before starting phase 2.

| Decision | Locked choice |
|----------|----------------|
| Phase 1 | Full wildlife predator–prey sim: maps, animals, crisp pixel art, readable play, and AI you can measure — rules and learning. |
| Phase 1 AI | FoV, influence / path costs, utility decisions, pack coordination, then a trained model (small neural policy or equivalent RL) that plays from the same limited observations. Experiments compare greedy, hand-written tactical, and learned. |
| Phase 1 content | 2 maps. Riverlands is tiger, wolf, and deer. Basin adds buffalo and one giraffe. |
| Phase 2 | One character battle in a Fire Emblem–like shape: named fighters, move then act, ranges, terrain. **No campaign, no story chapters, no supports.** |
| Phase 2 AI | Reuse the phase-1 pattern on battle rules: rule-based, shallow search, and a learned neural policy trained for that battle. Learning is not new in phase 2; the domain is. |
| Art / feel | The game loads PNG sprites, tiles, and UI images from `assets/`. Python may generate those files, but it does not draw animals at runtime. Integer scale, map-first UI, then juice that does not change sim state. Phase 2 reuses the same images. |
| Code shape | Modular and object-oriented. Core rules stay pure. Controllers, trainers, and chart reports are separate objects behind small interfaces. Pygame and matplotlib stay in adapters. |
| Results visuals | Every ML and AI comparison writes structured results, then a reports module draws charts (win rates, training curves, food and prey left). Figures are saved for the report and viewable without reading logs. |
| Process | SDLC per slice: requirements in this file and the GDD, a short design note, implementation, tests, then evaluation charts. A slice is not done until those steps exist. |
| Thesis (working) | Phase 1: under fog, a learned wildlife policy is compared with greedy and with influence-plus-utility rules. Phase 2: the same three-way comparison on one character battle. |
| Current slice | Straight steps cost 1 and diagonal steps cost 2. Buffalo can cross a river. A giraffe heals. Search stays off the ford until it sees an enemy. |
| Still open | Course deadline, demo length, product rename. |

## Changelog

| Date | Change |
|------|--------|
| 2026-10-02 | Adopted this document as the plan. Locked product, AI stack, content counts, art path, feel order, and module shape. |
| 2026-10-02 | Split delivery into two phases. Phase 1 is the full wildlife sim. Phase 2 is one character battle (not a campaign) plus ML / a small neural policy, after phase 1 is playable. |
| 2026-10-02 | Phase 1 also includes learning. Wildlife ships greedy, tactical rules, and a trained neural (or equivalent) policy, with experiments. Phase 2 repeats that pattern on one battle. |
| 2026-10-02 | Locked engineering rules: modular OOP with adapters, an SDLC slice checklist, and charts for ML and comparison results. |
| 2026-10-02 | Wrote `docs/PHASE1_BLUEPRINT.md`: rules kept, gaps, four roles, and the phase-1 done check. |
| 2026-10-02 | Slice 2: controller catalog, batch evaluation, result store, chart report, and pygame boundary. Design note: `docs/slices/02_folder_boundaries.md`. |
| 2026-10-02 | Runtime art is image files in `assets/`. Code-drawn animals stay only as a temporary stand-in. |
| 2026-10-02 | Slice 3: limited sight on observations, remembered tiles, influence in tactical scores, F1 fog and heat. Design note: `docs/slices/03_perception.md`. |
| 2026-10-02 | Replaced generated art with CC0 Tiny Creatures and Tiny Town images. Credits: `assets/CREDITS.txt`. |
| 2026-10-02 | Replaced the side panel and bottom bar with a centered board, a right-hand card stack, and a habitat title screen. |
| 2026-10-02 | Slice 6: basin map with one ford, and a buffalo herd beside the deer. Design note: `docs/slices/06_second_map.md`. |
| 2026-10-02 | Slices 7–9: offline wildlife network, three-way comparison charts, demo seed 7. Design note: `docs/slices/07_learned_policy.md`. |
| 2026-10-02 | Play menu: choose greedy, tactical, or learned, then predators or prey. The chosen policy plays the other side. Watch uses it on both. |
| 2026-10-02 | Slice 10: one-battle rules note. Move then act, rout win, six named fighters on wildlife bodies. Design note: `docs/slices/10_battle_rules.md`. Wildlife rules unchanged. |
| 2026-10-02 | Slice 11: skirmish map and roster data. Design note: `docs/slices/11_battle_roster.md`. Wildlife scenarios still load herds. |
| 2026-10-02 | Slice 12: rule-based skirmish controller. Move, then attack or wait. Design note: `docs/slices/12_battle_rules_ai.md`. |
| 2026-10-02 | Slice 13: two-ply skirmish search. Expected damage minus the best visible reply. Design note: `docs/slices/13_battle_search.md`. |
| 2026-10-02 | Slice 14: skirmish network in `config/policies/battle.json`. It refuses the wildlife weights. Design note: `docs/slices/14_battle_network.md`. |
| 2026-10-02 | Slice 15: skirmish cross-play charts. Seeds 0–3, 8 rounds: rules 13, learned 9, search 2, out of 16 each. Design note: `docs/slices/15_battle_charts.md`. |
| 2026-10-02 | Home menu Skirmish watches the one battle with rules, search, or the battle network on both sides. |
| 2026-10-02 | Skirmish menu can command hunters or the herd. The other side is rules, search, or the battle network. |
| 2026-10-02 | Skirmish presentation: the status line names the acting fighter, and the ford tiles are outlined. Search scoring was left as measured. |
| 2026-10-02 | A hit or kill pauses the picture for a moment, shakes the board, and shows the damage number. The match rules are unchanged. |
| 2026-10-02 | Diagonal steps cost 2. Buffalo can cross a river and are easier to hit if they stop there. A basin giraffe heals 10. Search stays off the ford until an enemy is visible. Remeasured skirmish, seeds 0–3: learned 10, rules 8, search 6 of 16. Design note: `docs/slices/16_leftover_rules.md`. |
| 2026-10-02 | Map terrain now uses the free Sprout Lands tiles by Cup Nooble. Animals stay Tiny Creatures. Grid size is unchanged. |

---

## 1. Two phases

The repo today is a **wildlife predator–prey sim** with light tactics chrome and rule-based AI. Finish that game before adding a character battle.

| Phase | What ships | What it proves |
|-------|------------|----------------|
| **1 — Wildlife** | Hunt, forage, fear, food, several animals and maps, crisp pixel presentation | Perception, influence, utility, and a trained policy, measured against greedy |
| **2 — One battle** | Named characters, one map, move then act, ranges and terrain | Search plus a second learned policy on battle rules |

Phase 2 steals Fire Emblem **battle** structure only:

| In phase 2 | Out of scope |
|------------|----------------|
| One battle, two sides | Campaign, chapters, world map |
| Characters with roles and stats | Supports, romance, permadeath meta |
| Move, then attack or wait | Weapon triangle and a huge class list |
| Attack range and terrain | Inventory economy |
| Win by routing the other side (or a simple seize tile if we add one) | Story scenes |

Do not start phase 2 until phase 1 is playable: you can watch or play a full wildlife match, the art reads at game size, and an experiment compares greedy, tactical, and learned controllers.

---

## 2. Can more algorithms be used meaningfully? Yes

Meaningful means each algorithm changes decisions or is measurable in experiments — not a name-drop.

| Algorithm | Why it belongs | What “done” looks like |
|-----------|----------------|------------------------|
| A* / BFS (present) | Movement under costs | Terrain-weighted costs, not flat 1 |
| Dijkstra / multi-source BFS (partial) | Food / threat distance fields | Reused every turn as maps |
| FoV / LoS (exists, unwired) | Imperfect information | Agents only act on seen tiles |
| Influence / threat maps (stub) | Pack + forage risk | Heatmap debug overlay + policy uses it |
| FSM / behavior tree | Readable roles (scout, flank, forage, flee) | Per-species or per-class trees |
| Utility / scoring AI (tactical already) | Tradeoffs | Documented weights; tunable |
| Minimax / expectimax (shallow) | 1–2 ply combat choices | Attack vs flank decisions |
| MCTS (light) | Harder positions | Optional hard AI mode |
| Q-learning / REINFORCE / evolutionary weights | Real learning claim | Train offline → compare vs baseline in experiments |
| Coordination assignment (wolf tiles already) | Multi-agent | Role assign; eval pack kill rate |

Do **not** implement all of them at once.

**Phase 1 stack (wildlife):**

1. Perception (FoV) so learners and rules see the same limited world
2. World model (influence + path costs)
3. Hand-written decision (utility + pack coordination) as the strong baseline
4. Learning: train offline a small neural policy (or RL such as DQN / policy gradient) for at least one side, using those observations as features
5. Evaluation: greedy vs tactical vs learned, same seeds, report wins, rounds, food, and prey left

**Phase 2 stack (one battle):**

1. Legal action generator for move-then-act
2. A search opponent (shallow minimax or expectimax)
3. A second learned network trained on battle observations, not a copy-paste of the wildlife weights
4. Same experiment harness: rules vs search vs learned

Lab narrative for both phases: **sense → model → decide → learn → measure**. Phase 2 changes the rules, not the idea that learning belongs in the product.

---

## 3. Can more maps and animals be added? Yes — if data-driven

Existing hooks: `config/map.json`, `units.json`, `scenario.json`, `tiles.json`.

**Maps**

- Multiple JSON maps (river choke, open plain, forest fog, island)
- Scenario packs: map + spawns + win conditions
- Optional later: simple map editor or generator

**Animals / units**

- Wire configured but unused roles first (buffalo water, giraffe support/heal) before inventing many new species
- Then add 1–2 roles that teach tactics, e.g. scout deer, tank buffalo, flanker wolf, ambush tiger

**Rule:** new unit = stats + one AI policy hook + one sprite family. No unit without an AI reason to exist.

**Phase 1 counts:** **2 maps**, **4 animal roles**. Phase 2 adds a separate character roster for the single battle; it does not replace the wildlife cast.

---

## 4. Can it look crisp, modern 2D pixel art? Yes — with a pipeline

Current look is weak because procedural sprites lack a locked palette/silhouette pass, UI competes with the map, and contrast/scaling are inconsistent.

**Crisp modern pixel needs**

- Locked palette (about 16–32 colors), one light direction
- 32×32 or 16×16 masters; **integer scale only** (2× / 3× / 4×); nearest-neighbor
- Those masters are PNG files in `assets/`. A Python script may create the files; the running game only loads them
- Silhouette-first animals readable at game size
- Quiet terrain; loud units + move / attack highlights
- UI: thin panel, sharp text at native resolution
- Optional idle / walk / attack frames (2–4) for perceived quality

Achievable in pygame-ce. An engine switch is not required for a lab demo. Art must be treated as product, not an afterthought. See also `VISUAL_DIRECTION.md`.

**Skills to use:** pixel-art-studio (author/critique loop), create-game-assets (brief + manifest + family consistency), game-ui-ux (HUD/menu stack), frontend-design principles adapted to game chrome (one composition, map-first).

---

## 5. Can gameplay feel good? Yes — mechanics first, then juice

For a tactics game, feel is mostly:

1. Clear affordances — what can move, where, what dies on confirm
2. Reversible planning — ghost path, damage preview
3. Snappy commit — confirm → feedback → next unit
4. Readable threat — attack ranges, danger tiles
5. Pacing — Detailed vs Fast without feeling broken

Then juice: short hit-stop, small shake, damage pop, feed sparkle, death fade — **visual only**, never mutating simulation state.

Without (1)–(4), juice only decorates a weak turn.

**Skills to use:** game-feel, game-ui-ux, pygame-core.

---

## 6. Why the battle comes second

Wildlife is the first place learning has to work: foggy observations, a tactical baseline, and a trained policy you can drop in as a controller. The battle comes after that loop exists.

Phase 2 is a better stage for explicit search (minimax-style), because move-then-act has cleaner action values. It gets its own network. It does not replace the wildlife simulation, and it is not the first time the project uses ML.

---

## 7. Modular OOP, SDLC, and charts

Keep the existing strength: core simulation without pygame. Structure the rest so a new AI, a new map, or a new chart does not require editing unrelated modules.

### Object-oriented rules

- One class, one job. `Simulation` does not train networks or draw charts. A `Controller` does not mutate the match. A `Trainer` does not open a window.
- Swap behavior through interfaces (Python protocols or abstract base classes): `Controller`, `Trainer`, `ResultStore`, `ChartReport`.
- Prefer composition. A match holds controllers; it does not subclass itself for “learned mode.”
- Domain objects (`Unit`, `Map`, `Action`, `Observation`, `MatchResult`) carry data and rules. Adapters translate those objects for pygame or for files.
- Shared helpers can stay functions. Do not wrap every line in a class.
- New phase-2 battle types implement the same controller and result interfaces. They do not fork the wildlife classes.

### SDLC for each slice

A slice is one row in the implementation order, not the whole game.

1. **Requirements** — what the slice must do, taken from this file or the GDD. If the goal changed, update the snapshot and changelog first.
2. **Design** — which classes and module boundaries are involved, written briefly in `docs/` or the slice note before the large edit.
3. **Implementation** — code only inside those boundaries.
4. **Test** — pytest for rules and controllers. Training code gets a small deterministic smoke test, not only a manual run.
5. **Evaluation** — if the slice changes AI or ML, write results and generate the charts below.
6. **Review** — check the slice against the requirement. Fix or record a plan change. Do not start the next slice on a broken test run.

### Charts

Numbers in a JSON file are not enough for the ML story. A `reports` adapter reads saved results and draws figures. The simulation and the trainer never import matplotlib.

Phase 1 figures, at minimum:

- Win rate by controller (greedy, tactical, learned)
- Training curve (reward or loss versus update)
- Prey remaining and food consumed, by controller
- Optional: a single-seed timeline of population and food

Phase 2 adds the same comparison chart for rules, search, and learned on the battle map.

Save images under `results/figures/` so the report and a results view can show them. A later in-game or menu screen may display those figures; it calls the reports adapter and does not recompute matches.

### Layout

```text
predator-prey-sim/
  config/                 # maps, units, tiles, scenarios only
  assets/                 # sprites, tilesets, fonts, sfx
  docs/                   # GDD, AI methods, architecture, art bible
  src/
    core/ or domain/      # rules, entities, win conditions (pure)
    ai/                   # perception, maps, policies, learning
      baselines/
      tactical/
      learned/            # model classes and inference only
    application/          # match setup, training use cases, experiment runner
    adapters/
      pygame_ui/          # rendering, input, menus only
      persistence/        # save and load result records
      reports/            # charts from result records
  tests/
  results/                # JSON/CSV plus figures/
```

Rules:

- Core never imports pygame or matplotlib
- One path to load config
- Controllers, trainers, and chart reports are swappable objects
- Maps and units are data, not hardcoded
- Experiment code writes records; only `adapters/reports` draws them

**Skills to use:** clean-architecture, pygame-core.

---

## 8. Skills checklist (use on purpose)

| Goal | Skill |
|------|--------|
| AI design | game-ai |
| Feel / juice | game-feel |
| Menus / HUD | game-ui-ux |
| Pixel art production | pixel-art-studio |
| Art direction / asset system | create-game-assets |
| Module boundaries | clean-architecture |
| Pygame loop / structure | pygame-core |
| Change critiques | review-agent (when implementing) |

---

## 9. Extra concerns often missed

1. **Rubric alignment** — What does the course mark? Search, agents, ML, report, demo? That chooses the algorithm stack.
2. **Thesis** — use the two working sentences in the snapshot. Update them when results exist.
3. **Evaluation is the AI proof** — comparisons need the charts in section 7, not only a win printed in the console.
4. **Scope kill list** — campaign is already out. Phase 1 stretch goals, at most two: buffalo water, giraffe heal. MCTS stays optional inside phase 2 search, not a third product.
5. **Audio** — a few SFX raise “real game” feel cheaply.
6. **Determinism** — keep seeded RNG; every AI claim needs replay.
7. **Debug as product** — FoV + influence overlay is a viva feature.
8. **Demo script** — a 3-minute seeded match that always looks good on stage.
9. **License / originality** — original pixel art or clearly licensed packs; no pasted commercial tactics assets.
10. **Balance** — predator-favored play makes AI look worse than it is; tune before big claims.
11. **Product name** — a sharper title than “Predator Prey Sim” helps the pitch if the product becomes tactics AI.
12. **AI usage** — encouraged here; still cite methods, keep experiments reproducible, and do not overclaim learning or intelligence.

---

## 10. Still open

These do not block phase 1. When one is decided, move it into the snapshot and log it in the changelog.

1. Course deadline and demo length
2. Product rename
3. Which phase-1 stretch goals, if any (at most two: buffalo water, giraffe heal)

---

## 11. Implementation order

### Phase 1 — wildlife

1. Wildlife blueprint: current rules kept, gaps listed (vision, influence, learning, art, second map)
2. Folder boundaries only where they unblock controllers, training, and assets
3. FoV on observations; influence maps in the tactical policy and the debug overlay
4. Pixel pipeline: palette, terrain, one prey, one predator; approve at game size, then the rest of the cast
5. Clear play: selection, legal moves, confirm, threat readability; then juice
6. Second map and the fourth animal role
7. Train a small wildlife network offline; load it as a controller object
8. Save structured results and generate the phase-1 charts
9. Phase 1 demo seed that can show the learned side and the figures

### Phase 2 — one battle, after phase 1 plays

1. Battle rules one-pager: characters, move then act, ranges, terrain, win condition
2. One battle map and a small character roster
3. Rule-based battle AI, then shallow search
4. Train a battle network offline; load it as another controller
5. Save results and generate the phase-2 comparison charts
6. Same art language; no campaign UI

---

## 12. Bottom line

- Phase 1 is the full wildlife game: classical agents, a trained model, maps, animals, pixel art, and feel.
- Phase 2 is one character battle, not a campaign, with its own search opponent and its own learned policy.
- Code stays modular and object-oriented: rules, controllers, training, and charts are separate.
- Each slice follows the SDLC checklist in section 7.
- ML claims are shown with saved charts, not only logs.
- Course AI assistance is encouraged; claims still need reproducible comparisons.

The planned slices are in. Further balance changes wait until you want them. If the plan changes, edit the snapshot and changelog in this file first.
