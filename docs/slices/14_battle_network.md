# Slice 14 — skirmish network

Requirements: a second network for the one battle. It does not load `config/policies/wildlife.json`.

## Design

Each legal action is one row of nine features: bias, progress toward the far side, the step, distance, whether it is a blow, the target's remaining health, ford cover, the nearest visible enemy, and which side is moving. Hidden enemies are not in the view, so they are not in the features.

`BattleLearnedController` scores those rows with the same small tanh network used for wildlife, but the input size is 9 instead of 8. Wildlife weights are refused. Play picks the highest score. Training samples and updates with REINFORCE. The hunter's return is herd health removed minus hunter health lost, plus a win or loss. Herd steps get the opposite advantage.

`python -m src.experiments.train_battle` writes `config/policies/battle.json`. The shipped file is 12 episodes, 8 rounds, seed 1.
