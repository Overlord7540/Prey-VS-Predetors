# Slice 7–9 — learned policy, charts, demo seed

Requirements: phase-1 slices 7, 8, and 9. One small network trains offline on the same limited observations as the other controllers. Experiments compare baseline, tactical, and learned. Figures are written by the reports adapter.

## Design

`PolicyNet` is a tanh hidden layer. Each legal tile becomes eight features: a bias, the step from the actor, distance, food, visible influence, nearest visible enemy, and side. The match still rejects anything outside `legal_destinations`.

`WildlifeTrainer` runs REINFORCE. The return is prey removed minus food eaten, plus a win or loss, from the predator's point of view. Prey actions get the opposite advantage. Training does not import pygame or matplotlib.

`LearnedController` loads `config/policies/wildlife.json`. Without those weights it refuses to act. With them, the catalog lists `learned` next to `baseline` and `tactical`.

`BatchEvaluation.compare` runs the three controllers on the same seeds. `python -m src.experiments.compare` writes `results/comparison.json` and the figures under `results/figures/`: win counts, prey left and food consumed, and the training curve.

The demo match is seed 7 on riverlands with the learned controller (`config/demo.json`):

```text
python -m src.main --seed 7 --controller learned
```
