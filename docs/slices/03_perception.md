# Slice 3 — field of view and influence

Requirements: phase-1 blueprint slice 3. Controllers act on limited observations. Match rules for fear, damage, and victory stay global.

## Design

`Simulation.observe` still copies live state, then `limit_awareness` trims that copy:

- A tile is visible inside `rules.sight_range` (default 6) when rocks do not block the line and tall grass does not conceal it past 3 tiles.
- Other animals and food outside that set are removed from the copy. The actor’s own tile stays visible.
- A herd goal outside sight is cleared on the copy so the baseline cannot walk toward hidden food.
- `InfluenceMap.radiate` writes a falloff from every visible enemy. Prey read it as danger. Predators read it as prey scent.
- The tactical prey score subtracts that value. Predator approach breaks distance ties toward higher scent.
- With no visible or remembered food, prey step toward tiles they have not seen. Sight is remembered after each decision, so the search does not circle the same window. Hidden food is never given before that tile has been seen.
- F1 draws fog outside the active animal’s sight and a heat tint for its influence. The overlay does not change the match.

Panic, despair, and attacks still use the live simulation, not the trimmed observation.
