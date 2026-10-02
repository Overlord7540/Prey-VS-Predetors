# Slice 16 — leftover rules

Requirements: the three tweaks left after the planned slices. No new campaign, and no change to how a hit is scored in search once an enemy is visible.

## Design

A straight step costs 1. A diagonal step costs 2. Both the wildlife match and the skirmish use that cost, so a diagonal is not a longer step for free. Corners stay blocked.

A buffalo may enter river tiles, up to two per activation. A ford is already walkable and does not spend that budget. Stopping on a river tile adds 8 damage to the next hit. Deer still cannot enter the river.

A giraffe regains 10 health at the start of its activation, capped at 100. Riverlands stays deer only. The basin match adds one giraffe beside the deer and buffalo.

Search still subtracts the strongest visible counter. Before anyone is in sight, it will not end a move on the ford if another tile is legal. The visible-enemy case that steps onto the ford to avoid a punished blow stays.
