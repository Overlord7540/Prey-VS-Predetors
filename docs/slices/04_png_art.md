# Slice 4 — first PNG art

Requirements: one terrain family, one prey, one predator, loaded from `assets/` at an integer scale.

## Design

Masters are 32×32 PNGs. `pixel-art/wildlife/build.py` is the source. The game never draws these three subjects with code.

| File | Subject |
|------|---------|
| `assets/tiles/open_field_0.png` … `_3.png` | Grass family, four variants, quiet edges |
| `assets/sprites/deer.png` | Prey |
| `assets/sprites/tiger.png` | Predator |

Other species and terrain stay on the old code drawings until the next art pass. The map zoom is 32 or 64, which is 1× or 2× the master. The menu vignette uses 32px tiles for the same reason.
