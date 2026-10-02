# Prey vs Predators

**A turn-based wildlife simulation and one duel, used to compare rule-based, search, classical, and learned game AI**

Course: CSE 3812, Artificial Intelligence Laboratory  
Date: 3 October 2026

---

## Abstract

Prey vs Predators is a turn-based game in which hunters and a herd share one meadow, and, in a second mode, two predator packs fight on a closed board. The same match can be commanded by a person or by one of several artificial players. Three original players are always available. Calm takes the nearest gain. Wary scores sight, danger, food, and pack movement. Sharp is a small neural policy trained by REINFORCE. Five further players — logistic regression, a decision tree, a random forest, naive Bayes, and a Markov model — are trained only to imitate Wary’s tile choices, then graded on matches of their own.

On the recorded Riverlands comparison (seeds 0–3, 40-round cap, both sides using the same player), Calm split 2–2, Wary won 3 of 4 as the hunters, and Sharp won all 4. Extra training raised Sharp’s episode score from about −0.09 to 0.28, and the hunter win count on those four seeds stayed at 4 of 4. The five imitators match Wary on 4% to 38% of held-out moves. Guessing a legal tile is about 4%. When both sides of a match use one imitator, the hunters won none of the four seeds. On the duel, tiger pack against jackals, Calm won 11 of 16 cross-play games, Wary 8, and Sharp 5.

The simulation does not import the display library. Pygame draws the board. Matplotlib draws the charts. A Windows executable is built from the same entry point.

---

## 1. Introduction

The laboratory asks for more than a single pathfinding demo. A game is a useful setting because every decision is visible, the rules are fixed, and two different methods can be given the same board, the same seed, and the same time limit.

This project uses that setting twice.

The meadow is a predator–prey ecology. Hunters win by taking down enough of the herd. The herd wins by eating enough of the food. Animals do not see the whole map. Rocks block sight. Tall grass hides distant animals. A straight step and a diagonal step do not cost the same. A person can command either side, or watch.

The duel is one battle, not a campaign. Three named tigers and wolves face three named jackals. There is no food and no fear state. A side wins by clearing the other. The duel reuses the idea of Calm, Wary, and Sharp, but the algorithms are the battle versions: a rule controller, a two-ply search, and a second neural policy that never loads the meadow weights.

The teaching aim is that each method has one job a viewer can point at.

| Player in the menu | What it actually is | What it is for |
| --- | --- | --- |
| Calm | Greedy rules on the meadow; a scripted fighter in the duel | A simple baseline |
| Wary | Scored tactics on the meadow; two-ply search in the duel | A stronger hand-written player |
| Sharp | A neural policy trained by self-play | A player that improves from match outcomes |
| The five students | Copies of Wary’s tile choices | Classical models, checked on moves they did not train on |

Player clicks are not written into Sharp’s weights. A human game is a game. Training is a separate, seeded batch.

---

## 2. Objectives

1. Build a seeded, headless simulation whose rules do not depend on the window.
2. Let a person play either side with the same movement and combat rules the AI uses.
3. Give every animal a limited view, and make Wary use that view.
4. Put three difficulties in front of the player, and keep the algorithm names available in Field notes.
5. Train a neural policy on whole matches, save the weights, and show whether more episodes change the win count.
6. Train five classical models to imitate Wary, report accuracy against chance, and also report match wins.
7. Add one closed duel with its own controllers, its own network, and its own chart.
8. Keep results as JSON and as figures, so a report does not depend on reading a log.

---

## 3. The game

### 3.1 Meadow

A match is a sequence of rounds. In a round the hunters act, then the herd acts. Inside a side, animals act one at a time. Detailed playback shows each action. Fast playback resolves a whole round, and still stops when it is the person’s turn.

The person clicks an animal, then a highlighted tile. The animal is shown on that tile, and a small card offers Attack, Feed, Wait, or Cancel. Attack shows a damage range before the blow is confirmed. Feed is offered only to prey standing on food. Cancel drops the destination and keeps the animal selected. Escape clears the whole plan. End turn makes every unused animal wait, without an automatic attack or bite of food.

Win conditions, read from the map:

- Hunters win when eliminated prey reach 70% of the starting herd. The count is compared as a fraction of the starting number.
- The herd wins when consumed food reaches 65% of the starting stock.

If the round cap is hit first, the match is unfinished. Experiments record that outcome instead of inventing a winner.

Six clearings are selectable from a horizontal carousel. Each of Glade, Rocks, and Ford opens with a lesson. Dawn, Noon, and Dusk are three layouts of the same animals. Noon is the layout written in the scenario file. Dawn and Dusk move those animals. The playable game defaults to the large board where a large file exists. Riverlands large is 20×20. The headless comparison in this report uses the Riverlands scenario loader, which is the 12×10 board. Those two boards are not the same measurement.

| Clearing | What it adds |
| --- | --- |
| Glade | Open grass. The lesson is movement range. |
| Rocks | A stone wall. The lesson draws sight fog for the acting animal. |
| Ford | A river, and a buffalo that can wade. |
| Riverlands | The wide meadow: a tiger, two wolves, and deer. This is the training map. |
| Basin | A buffalo herd and one giraffe. The giraffe regains 10 health at the start of its activation, up to its maximum. |
| Rookery | Two hares, one heron, and two jackals. The hare spooks at a longer range. The heron sees farther than it steps. |

Species on the meadow:

| Species | Side | Health | Move | Damage | Notes |
| --- | --- | --- | --- | --- | --- |
| Tiger | Hunter | — | 3 | 32±10 | Solitary |
| Wolf | Hunter | — | 2 | 22±6 | Pack. Cooldown 1 after a kill |
| Jackal | Hunter | — | 2 | 16±4 | Pack of two on Rookery |
| Deer | Herd | 40 | 2 | — | Can spend 1 step in water |
| Buffalo | Herd | 60 | 2 | — | Can spend 2 steps in the river. Stopping in the channel adds 8 exposure to incoming damage. Eats 2 |
| Giraffe | Herd | 100 | 2 | — | Heals 10 at the start of its activation on Basin |
| Hare | Herd | 24 | 2 | — | Panic range 8 |
| Heron | Herd | 28 | 1 | — | Sight 8 |

A straight step costs 1. A diagonal step costs 2. Occupied tiles are blocked. A diagonal cannot squeeze between two blocked corners. Hunters do not enter the river. Buffalo may. The first damaging hit on an animal at full health cannot kill it if it has more than 1 health. The survivor bolts to a reachable tile that maximizes distance from living hunters, and other hunters cannot target it until its next activation.

Fear is a herd state, not a replacement for the person’s command. Nearby hunters can push a flock from calm into panic, and a blow can push it into despair. Despair prefers distance from hunters and closeness to a living flockmate. Wary’s prey score uses those states. The person’s click does not.

### 3.2 Duel

The duel is three against three.

| Name | Body | Side | Health | Move | Damage |
| --- | --- | --- | --- | --- | --- |
| Sable | Tiger | Tiger pack | 48 | 3 | 32±10 |
| Ash | Wolf | Tiger pack | 36 | 4 | 22±6 |
| Birch | Wolf | Tiger pack | 36 | 4 | 22±6 |
| Cinder | Jackal | Jackals | 36 | 4 | 20±6 |
| Nettle | Jackal | Jackals | 36 | 4 | 20±6 |
| Bramble | Jackal | Jackals | 42 | 3 | 22±6 |

Internally the sides are still called hunter and herd, so the battle network’s side bit does not have to change. The screen says Tiger pack and Jackals.

Three grounds share that roster. Field is open, with sight 12, so the packs start able to see each other. Ford is the river skirmish. Stone is a rock wall with gaps at the ends; sight is 12, and the wall, not the range, hides the other pack. Large and small versions exist. The playable game defaults to large. The recorded duel chart uses the small Ford board, which is what the headless battle builder loads by default.

A fighter moves, then attacks or waits. Standing on a ford tile gives cover: incoming damage is reduced. The side that clears the other wins. There is no food, no feeding, and no flee.

### 3.3 How a person meets the AI

The front door is New game, Field notes, or Settings. New game asks for the meadow or the duel. The meadow asks for a clearing, then Calm, Wary, or Sharp, then an optional study of the five imitators, then a side: command the hunters, command the herd, or watch. The duel asks for a ground, then the same three difficulties, then the tiger pack, the jackals, or watch.

Field notes are sentences, not a log. They name the three original players, the neural score at the start and end of training, the hunter wins before and after the extra episodes, and, for each imitator, how often it picked Wary’s tile and how often the hunters won when both sides used it.

The tile grid is off until G is pressed. The camera eases toward the animal that is acting. A goal line fades after the opening seconds. A step, a bite, and feeding each have a short sound. While an opponent acts, a card names the mind, what that animal could see, the step it took, and the step it turned down.

---

## 4. Architecture

The rule that keeps the project testable is the dependency direction. Core code decides what is legal. It does not draw, and it does not import Pygame or Matplotlib. AI code reads a detached observation and returns an action. It does not apply damage. The window and the charts sit outside that core.

```
config/          maps, species, scenarios, battles, saved weights
src/core/        grid, movement, combat, sight limits, turns, simulation, battle
src/ai/          greedy policy, tactics, pathfinding, sight, influence
                 classical models, meadow network, battle network, battle search
src/application/ training and seeded evaluation
src/adapters/    pygame boundary, result files, matplotlib charts
src/rendering/   window, camera, menu, commands, sprites
src/experiments/ command-line train and compare
tests/           rules, menus, policies, training
```

An observation is a copy. A controller cannot move an animal by editing the copy. The simulation checks the destination against the live movement range. A malformed action is rejected. A well-formed destination that is no longer legal becomes a wait.

Controllers are chosen by name from a catalog: `baseline`, `tactical`, `learned`, `logistic`, `tree`, `forest`, `bayes`, `markov`. A side override replaces the default. An individual animal override replaces the side. The person’s side is not given a controller. Watch mode gives the chosen controller to both sides.

Seeds own the random sequence for placement, intent, damage, and, during training, exploration. Two runs with the same seed and the same code produce the same match. Training that resumes does not repeat the old episode seeds: new episodes are numbered after the saved curve.

---

## 5. Perception and movement search

### 5.1 Sight

Most maps set sight range to 6. The heron uses 8. Field and Stone duels use 12 so that a wall, not the range, is what hides a fighter. An animal remembers tiles it has seen. The observation given to a controller is limited to the current view plus that memory. The person still sees the whole board. F1 draws fog and an influence heat map for the acting animal. The Rocks lesson draws the fog even when F1 is off.

Line of sight stops on rock. Tall grass conceals an animal beyond three tiles. Sight range is applied when the visible set is built. A bare line-of-sight test, without the range, is not “the animal sees the map.”

### 5.2 Pathfinding

Two searches are used, and they answer different questions.

Breadth-first search computes distance to a set of tiles, usually food or a goal, while treating occupied tiles as blocked. Wary uses those distance fields when it scores a herd move and when wolves share an approach.

A* searches a path for the greedy hunter. The step cost is the movement cost above: 1 orthogonal, 2 diagonal. If A* fails, the hunter steps to the passable, unoccupied neighbor closest to the goal instead of freezing.

When a hunter can see no enemy, duel search drops ford tiles from its destinations if any other legal tile exists. It will still step onto the ford once an enemy is visible. That rule exists so a blind fighter does not finish its turn standing in the channel.

### 5.3 Influence

Wary builds an influence value on tiles it can reason about. The meadow feature vector later gives Sharp one number from that map: influence at the candidate tile, divided by sight range. Influence is a summary of pressure, not a second pathfinder.

---

## 6. The three meadow players

### 6.1 Calm

Calm is the greedy baseline.

A hunter with prey in its limited view picks the nearest living prey by Chebyshev distance and walks toward it. Intent at setup is chase, ambush, or camp, with the species bias weighted more heavily. Camp used to plant the hunter on the far side of a river even when that tile was no closer to the prey. It now chases when the camp tile is not an improvement, when the prey is already within three tiles, or when the map has no river. If no prey is visible, the hunter steps toward tiles it has not seen.

A herd animal routes toward food with A*, then BFS if that route is blocked. Panic ranks neighbors by distance from the hunter and closeness to food. Despair ranks distance from the hunter and closeness to a flockmate. Food underfoot is eaten when that is safe. Calm does not publish a second-best tile. The decision card says so.

### 6.2 Wary

Wary is the default opponent.

Hunters that can attack from a reachable tile do that first. The preferred target is the unprotected prey with the lowest health, then the shorter step. Wolves that share a pack choose a prey by the sum of approach distances, then take distinct adjacent tiles. Equal-length approaches prefer to stay apart. The assignment is recomputed for each animal, because an earlier wolf may have moved. Jackals on Rookery are a pack in the same sense. A pack step is kept only when it actually leaves the current tile, so a failed team plan does not freeze the animal.

If there is no attack and no useful pack step, the hunter walks a distance field toward the prey, biased by influence.

Herd animals score every legal tile, including waiting. Standing next to a ready hunter is heavily punished. Predicted exposure on the hunter’s next turn is punished less. Food distance comes from the BFS field. Panic increases the weight of escape. Despair adds a pull toward the flock. If the current tile has food and the score says it is safe, the animal eats. The second-best tile is kept, and the decision card can say which way that step pointed.

### 6.3 Sharp

Sharp is one network for both sides. It does not see the board as a picture. For every legal tile it builds eight numbers:

1. A constant 1, so the output can shift.
2. Row offset, divided by the map height.
3. Column offset, divided by the map width.
4. Chebyshev distance from the animal, divided by sight range.
5. Food on that tile, divided by 2.
6. Influence on that tile, divided by sight range.
7. Distance from that tile to the nearest visible enemy, divided by sight range. If no enemy is visible, this is 1.
8. 1 if the animal is a hunter, otherwise 0.

The network has 8 inputs, 8 hidden units with a tanh activation, and one output score per tile. At play time it takes the highest score. Ties break toward the earlier tile.

Those features are relative. They do not remember the tile the animal just left. On Rookery at dusk the jackals can stand on the north bank, see nobody, and find that “stay” wins by a few thousandths. The match then looks frozen. During play, if Sharp chooses the current tile, sees no enemy, and is not standing on food, it instead steps toward unseen ground. That exception is not used while the network is exploring in training, so the learning signal still matches the sampled action.

---

## 7. How Sharp learns

Training is offline REINFORCE. There is no window. Both sides of a Riverlands match use the same network. While training, a tile is sampled from the softmax of the scores. The chosen index, the hidden activations, and the probabilities are stored. At play time nothing is sampled and nothing is written back.

At the end of the episode the return is from the hunters’ point of view:

```
(prey killed / prey at the start)
− (food eaten / food at the start)
+ 1 if the hunters won, −1 if the herd won, 0 if the match was unfinished
```

An exponential moving baseline tracks that return: 90% of the old baseline plus 10% of the new return. The advantage is the return minus the baseline. Hunter samples are trained toward the advantage. Herd samples are trained toward the opposite, because a good herd outcome is a bad hunter outcome. Credit is spread across every stored move in the episode. The learning rate is 0.08.

The first saved run was 20 episodes. Training was then resumed for 60 more episodes, 20-round cap, seed 1, on Riverlands. The file now holds 80 episode scores. Resume loads the matrices; it does not start from a new random network. Episode seeds continue after the old curve, so the new matches are not copies of the first 20.

The same four evaluation seeds are played before the extra training and again after the new weights are saved. That order matters. Evaluating “after” before the save would reload the old file and report no change.

Sharp’s play heuristic, the step toward unseen ground, is outside this loop. The weights do not contain the player’s clicks.

The duel has a second network. It has 9 inputs: bias, forward offset, sideways offset, distance, whether the action is an attack, the target’s remaining health, whether the destination is a ford, distance to the nearest visible enemy, and a side bit. It is trained the same way, for 12 episodes, with a return based on health lost by the other side minus health lost by the tiger pack, plus win or loss. It refuses the meadow file. It was not retrained when the duel roster became jackals. The win table in this report is a new measurement of those saved weights.

---

## 8. The five imitators

These models do not play to win during training. They watch Wary and learn to pick the same tile.

On the saved run, Wary played 2 Riverlands matches of up to 8 rounds. That produced 120 decisions. The last fifth, 24 decisions, was held out. The first 96 were the training set. For every decision the features are the same eight numbers Sharp uses, one row per legal tile, and the label is the index Wary chose.

Each model scores every legal tile. The highest score is its choice. Accuracy is the fraction of held-out decisions where that choice is Wary’s tile. Chance is the average, over those decisions, of 1 divided by the number of legal tiles. On this holdout, chance is 4.3%. A model is counted as improved when its accuracy is more than two percentage points above chance.

| Model | What it stores | Held-out match to Wary | Against 4.3% chance |
| --- | --- | --- | --- |
| Logistic regression | One weight per feature, plus a bias, fit by gradient steps on a sigmoid | 29.2% | Clearly better |
| Decision tree | Depth 3, splits chosen by information gain | 37.5% | Clearly better |
| Random forest | 5 trees, each on a bootstrap sample and 4 random features | 25.0% | Clearly better |
| Naive Bayes | Mean and variance of each feature for the chosen class and the rest | 16.7% | Clearly better |
| Markov model | Counts of step direction given a coarse situation and the previous direction | 4.2% | Not better |

The Markov model is the only one with memory of the previous step. Its situation is coarse: whether the tile has food, and banded values for enemy distance, influence, and side. On this small holdout it did not beat guessing.

Copying a tile is not the same as winning a match. After the weights were frozen, each imitator played both sides of seeds 0–3 for up to 40 rounds. The hunters won none of those 16 games. Logistic regression finished two for the herd and left two unfinished. The tree and the Markov model left all four unfinished. The forest left three unfinished and lost one to the herd. Naive Bayes lost three to the herd and left one unfinished. The Field notes say both facts: the copy rate, and the win count.

---

## 9. The duel players

Calm in the duel is a script. It advances, attacks when a blow is legal, and holds when the advance is not useful.

Wary in the duel is a two-ply search. For each legal move or attack it copies the board, applies the action, and scores the result against the best reply it can see. The score prefers expected damage dealt, then penalizes the opponent’s best answer. Progress down the board and useless drifting are part of the key. When no enemy is visible, ford destinations are removed if any other tile exists.

Sharp in the duel is the 9-input network above. Play is again the highest score. Training samples from the softmax.

Cross-play is every pairing. For seeds 0–3, each player meets each of the other two, once on each side. That is 16 games per player. The cap is 8 rounds. Every recorded game finished.

---

## 10. Experiments

### 10.1 Meadow, same player on both sides

Command: `python -m src.experiments.compare --seed 0 --matches 4 --max-rounds 40`

Board: Riverlands through the headless scenario loader, 12×10, Noon layout. This is not the 20×20 board the window uses by default.

| Player | Hunter wins | Herd wins | Unfinished | Mean prey left | Mean food eaten |
| --- | --- | --- | --- | --- | --- |
| Calm | 2 | 2 | 0 | 2.75 | 21.00 |
| Wary | 3 | 1 | 0 | 2.00 | 21.25 |
| Sharp | 4 | 0 | 0 | 1.00 | 13.75 |

Sharp’s four wins took 8, 6, 6, and 7 rounds, and each ended with one prey still alive. That is the elimination threshold, not a total wipe. The herd ate less food in those short matches, which is why the food column is lower. A lower food number here means the match ended before the herd could finish eating. It does not mean Sharp is a better forager.

Figures: `results/figures/win_rates.png`, `results/figures/prey_and_food.png`, `results/figures/training_curve.png`. The numbers are in `results/comparison.json`.

### 10.2 Sharp, before and after more episodes

The evaluation is seeds 0–3, 40-round cap, both sides Sharp, on the same Riverlands loader.

| | Hunter wins |
| --- | --- |
| After the first 20 episodes | 4 of 4 |
| After 60 more episodes (80 stored) | 4 of 4 |

The training score, which is the hunter return above, started at −0.09. It was 0.06 at episode 20. It was 0.28 at episode 80. The curve is noisy. Single episodes still swing from about −1.5 to about 1.5, because a win and a loss dominate the return and the credit is spread across every move.

The honest reading is that the extra episodes moved the training score up, and they did not change the win count on this four-seed test. Sharp was already winning all four before the resume. Four seeds cannot show a finer improvement.

### 10.3 Imitators, copy score and match score

Held-out tile match is Section 8. Match results, both sides the same imitator, seeds 0–3, 40 rounds:

| Model | Hunter wins | Herd wins | Unfinished |
| --- | --- | --- | --- |
| Logistic regression | 0 | 2 | 2 |
| Decision tree | 0 | 0 | 4 |
| Random forest | 0 | 1 | 3 |
| Naive Bayes | 0 | 3 | 1 |
| Markov model | 0 | 0 | 4 |

A model can imitate Wary on a third of held-out moves and still fail to close a match. Wary’s strength is the whole policy, including attacks and the second-best reasoning around food. The imitators only see the chosen tile’s features. They do not receive Wary’s reason, and they do not plan past one step. The Markov model, which does keep a previous direction, was the weakest copy on this sample.

### 10.4 Duel, tiger pack against jackals

Command: `python -m src.experiments.compare_battle`

Board: the default small Ford skirmish. Roster: Sable, Ash, Birch against Cinder, Nettle, Bramble. Seeds 0–3. Cap 8 rounds. Each cell is that player’s wins across 16 games, counting a win on either side.

| Player | Wins | Losses | Unfinished | Mean own health left | Mean other side’s health left |
| --- | --- | --- | --- | --- | --- |
| Calm | 11 | 5 | 0 | 28.2 | 5.8 |
| Wary | 8 | 8 | 0 | 17.4 | 26.2 |
| Sharp | 5 | 11 | 0 | 13.3 | 26.8 |

Calm is the strongest of the three on this measurement. Sharp is the weakest. That is the opposite of the meadow table, and it should be. The duel network was trained for 12 episodes and was not retrained after the opposing pack became jackals. The meadow network was trained for 80 episodes on Riverlands, which is a different game. Sharing the nickname Sharp does not mean the two networks share weights.

Figures: `results/figures/battle_wins.png`, `results/figures/battle_health.png`, `results/figures/battle_training.png`. The games are in `results/battle_comparison.json`.

---

## 11. Discussion

The meadow ranking matches the design. Calm wins some matches because nearest-food and nearest-prey are already reasonable on an open board. Wary wins more as the hunter because it will not spend the turn on a tile that is merely nearby, and because the wolves share an approach. Sharp wins the four recorded seeds because self-play on this map, with a hunter-shaped return, rewards finishing the herd before the food is gone. Its matches are shorter and the herd eats less. That is a hunter-favored policy, not evidence that the herd side failed to learn. The herd is trained by the negated advantage, so a herd win does teach the herd samples. The return’s shape still cares more about hunter victory than about a long, careful feeding game.

The imitators are the right lesson for a laboratory and a weak lesson if someone expects them to replace Wary. They are supervised copies of one player’s tiles. Four of five beat chance, which is the claim the training procedure was built to test. Their match record, zero hunter wins, is the claim a separate play grade was built to test. Both belong in the report. Reporting only the 37% tree accuracy would hide the fact that the tree did not finish a game.

The duel ranking is a warning against reusing a nickname. Twelve episodes of battle self-play, measured later on the jackal roster, do not beat a short script. Search lands in the middle. A two-ply reply is enough to avoid some bad trades and not enough, on this sample, to beat Calm’s direct advance. The sample is 16 games. It is large enough to see the order Calm, then Wary, then Sharp. It is not large enough to quote a stable percentage for a larger tournament.

Several meadow maps still lean. Ford with Wary, and the small Basin with Wary, favor the hunters more than a coin flip. The large Basin with Calm often eats very little. Those leans were left in place after earlier layout changes started to make other maps a sweep. The four-seed Riverlands table should not be read as a balance certificate for every clearing.

Sharp’s idle step on unseen ground is a play rule, not a weight. It stops the Rookery dusk freeze, where both jackals waited on the north bank because “stay” won by a hair and the herd was out of sight. It does not retrain the network.

---

## 12. How to reproduce

From the project directory, with Python 3:

```powershell
python -m pip install -r requirements.txt
python -m src.main
python -m pytest tests
python -m src.experiments.train --resume --episodes 60 --max-rounds 20 --seed 1
python -m src.experiments.compare --seed 0 --matches 4 --max-rounds 40
python -m src.experiments.compare_battle
```

`train --resume` continues Sharp from `config/policies/wildlife.json`. Without `--resume`, a run starts from a new network and replaces that file. The five imitators are trained from Field notes, or from `python -m src.experiments.train_classical`. Grading their wins does not, by itself, refit them. The duel network is trained by `python -m src.experiments.train_battle` and is a different file, `config/policies/battle.json`.

The window executable is `dist/Prey vs Predators.exe`. It is a one-file build of the same game. Rebuilding it requires PyInstaller and a closed copy of the old exe, because Windows will not replace a program that is open. The first launch unpacks, so it is slower than later clicks. Training from inside the executable is not the reproducible path. The commands above are.

Dependencies for the game and the tests are pygame-ce, pytest, and matplotlib. The neural net and the five models are implemented in the project. scikit-learn is not used.

Tests cover movement costs, sight, combat, the escape after a non-lethal hit, menu navigation, the duel maps, the command card, training determinism when resume is off, and the Rookery dusk case where Sharp must leave the north bank.

---

## 13. Limits

- The published meadow chart is four seeds on the 12×10 Riverlands loader. The window’s default Riverlands is 20×20. A result on one board is not a result on the other.
- Sharp’s win count did not move when training went from 20 to 80 episodes, because it was already 4 of 4. A larger seed set would be required to see anything smaller than a sweep.
- The five models were fit on 96 decisions. That is enough to beat a 4% chance on a 24-decision holdout. It is not a large behavioral clone of Wary.
- The duel network was not retrained for the jackal roster. Its chart is a measurement of the saved 12-episode weights.
- Human games are not a training set.
- There is no campaign, no save of a half-finished match, and no mixing of meadow weights into the duel.
- Terrain art is from the Sprout Lands pack by Cup Nooble, used under that pack’s non-commercial terms. The animals are original drawings for this project. The title screen does not carry a social-media handle.

---

## 14. Conclusion

The project is a playable game whose difficulties are distinct algorithms, plus a record of what those algorithms did under a fixed seed list.

On the meadow, greedy play splits the four Riverlands seeds, scored tactics win three as the hunter, and the neural policy wins all four. Continuing training raised the episode score and left that sweep unchanged. Five classical models can be shown, in one sentence each, to copy Wary better than chance or not, and in a second sentence to fail as hunters when they have to play the match themselves. On the duel, the script beats the search, and the search beats the small battle network.

That split is the result the laboratory can stand on. Each method is visible in the menu, explained in Field notes, and backed by a JSON file and a figure. The simulation that produces those files does not depend on the window that plays them.

---

## References

Hart, P. E., Nilsson, N. J., and Raphael, B. “A Formal Basis for the Heuristic Determination of Minimum-Cost Paths.” *IEEE Transactions on Systems Science and Cybernetics*, 1968. The meadow hunter’s route search is A* with the project’s step costs.

Sutton, R. S., and Barto, A. G. *Reinforcement Learning: An Introduction*. MIT Press. Sharp’s update is the REINFORCE policy gradient, with a moving baseline and a return defined in Section 7.

The logistic, tree, forest, Bayes, and Markov players are small implementations written for this project. Their definitions are in `src/ai/classical/models.py`. They are not a claim that a library’s full algorithm, with its usual hyperparameters, was run unchanged.

---

## Appendix A. Where the numbers live

| Claim in this report | File |
| --- | --- |
| Meadow wins, prey left, food eaten, training curve | `results/comparison.json` |
| Meadow figures | `results/figures/win_rates.png`, `prey_and_food.png`, `training_curve.png` |
| Sharp’s 80 episode scores and the 4-of-4 before/after wins | `config/policies/wildlife.json` |
| Imitator accuracy, chance, and match outcomes | `config/policies/classical.json` |
| Duel cross-play | `results/battle_comparison.json` |
| Duel figures | `results/figures/battle_wins.png`, `battle_health.png`, `battle_training.png` |
| Duel network | `config/policies/battle.json` |

## Appendix B. Feature vectors

Meadow, eight numbers, one row per legal tile: bias, row offset, column offset, distance from the actor, food, influence, distance to the nearest enemy, side.

Duel, nine numbers, one row per action: bias, forward offset, sideways offset, distance from the actor, attack or not, target health, ford or not, distance to the nearest enemy, side.

Both vectors are scaled into a small range so a weight has a comparable meaning across maps of different sizes. Neither vector includes the animal’s previous tile. Memory of the last step exists only in the Markov imitator, and in the play-time checks that stop an immediate reverse or an unexplained wait.

## Appendix C. Every AI and machine-learning method

Each entry says where the code lives, when it runs, and how it is used. “Play” means a match on screen or in a headless evaluation. “Training” means an offline batch that writes a saved file.

### Shared by every animal, including the person

**Uniform-cost move range.** `src/core/movement.py`. Used whenever anyone asks which tiles an animal can reach: the person’s highlights, Calm, Wary, Sharp, and the five imitators. A frontier spreads from the animal. A straight step costs 1 and a diagonal costs 2. Occupied tiles and blocked corners are skipped. Buffalo may spend a limited number of steps in the river. The search stops when the movement budget is spent.

**Chebyshev distance.** `src/core/grid.py`. Used whenever the game asks “how many king-steps apart are these two tiles?” Attack range is a distance of 1. Calm picks the nearest prey with it. The feature vectors divide a Chebyshev distance by sight range.

**Bresenham line of sight.** `src/ai/fov.py`. Used while building what an animal can see, before any controller chooses. A line of tiles is walked from the animal to the target. A rock on that line blocks the target. Tall grass hides a target more than three tiles away.

**Limited view and memory.** `src/ai/awareness.py`. Used on every AI decision, after the legal tiles are listed and before the controller is called. Enemies, food, and tiles outside the current view are removed, except tiles this animal has already seen. The person is not filtered. The window still draws the whole board.

### Meadow — Calm (greedy rules)

**Random intent at birth.** `src/ai/fsm.py`, `roll_intent`. Used once, when the match is created, for each hunter. The species bias (camp for the tiger, ambush for the wolf and the jackal) is twice as likely as the other intents. The intent is chase, ambush, or camp.

**Greedy target choice.** `src/ai/fsm.py`, `select_target`. Used by Calm whenever a hunter can see prey. The nearest living prey by Chebyshev distance is the target. A tie keeps the earlier animal in the list.

**A\*.** `src/ai/pathfinding.py`. Used by Calm to walk a hunter toward a chosen tile, and to walk a herd animal toward food. The cost of a step is the movement cost above. Occupied tiles are walls. If no path exists, the hunter steps to the open neighbor closest to the goal instead of standing still.

**Breadth-first search to food.** `src/ai/pathfinding.py`, `nearest_resource` and `bfs_shortest_path`. Used by Calm when the first food route is blocked. The search expands in rings until it finds a stocked tile that can be reached.

**Prey state machine.** `src/core/perception.py` together with `src/ai/fsm.py` and `src/ai/pathfinding.py`. The simulation sets the state before the herd animal acts. Calm then uses it. Panic, when a hunter is inside the panic range, ranks tiles by distance from that hunter plus closeness to food. Despair, after a blow to the flock, ranks distance from hunters plus closeness to a living flockmate. A calm animal routes to food. Safe food underfoot is eaten instead of leaving.

**Camp, chase, and ambush.** `src/ai/fsm.py`, `step_predator_solo`. Used only by Calm hunters. Chase walks toward the prey. Ambush walks toward the midpoint of the prey and its nearest food. Camp aims across the river, but switches to a direct chase when that camp tile is no closer, when the prey is already within three tiles, or when the map has no river.

**Look toward unseen ground.** `src/ai/tactics.py`, `explore_beyond_sight`. Used by Calm when no prey is in view. Each legal tile is scored by how many new tiles would become visible from there. The best tile is taken. Sharp uses the same function during play, and only then, when its network chose to wait, no enemy is visible, and the animal is not standing on food. Training does not use it.

### Meadow — Wary (scored tactics)

**Multi-source breadth-first distances.** `src/ai/tactics.py`, `distances`. Used on each Wary decision that needs “how far is food?” or “how far is this attack tile?” One search starts from many tiles at once. Occupied tiles are blocked. The result is a distance number on every reachable tile.

**Herd utility score.** `src/ai/tactics.py`, `forage_safely`. Used whenever Wary moves a herd animal. Every legal tile, including staying, gets one number. Standing next to a ready hunter is a large penalty. A hunter who could arrive next turn is a smaller penalty. Food that is closer is a bonus. Panic raises the value of escape. Despair adds a pull toward the flock. The highest tile is taken. The second highest is remembered for the decision card. Food underfoot is eaten when that tile’s danger term is zero.

**Influence map.** `src/ai/influence_map.py`. Built fresh for one observation. It is not stored on the match. Each visible enemy spreads a value that falls off with Chebyshev distance, and only onto tiles the animal can see. Wary’s hunter uses the number when breaking ties. Sharp and the five imitators receive it as feature 6.

**Pack assignment.** `src/ai/tactics.py`, `coordinated_wolf`. Used when Wary moves a hunter whose pack id is set: the two wolves, and the two jackals on Rookery. The prey is the one the pack can approach for the least total distance. Each wolf is given a different adjacent tile. Equal-length approaches prefer to stand apart. The plan is rebuilt for every animal, because the previous wolf may already have moved. If the plan says “stay,” it is thrown away and the hunter uses the ordinary hunt instead.

**Hunter utility after the pack step.** `src/ai/policies.py`, `TacticalController`. Used when there is no legal bite and no useful pack step. A distance field is built toward the prey. The legal tile with the smallest distance wins. Influence and a shorter step break ties.

### Meadow and duel — Sharp (neural policy and REINFORCE)

**Hand-built feature vector.** `src/ai/learned/features.py` on the meadow, `src/ai/learned/battle_features.py` in the duel. Built for every legal tile, or every duel action, immediately before the network or an imitator scores it. The meadow vector has the eight numbers in Appendix B. The duel vector has the nine. This is the only picture of the board those models get.

**Feedforward network.** `src/ai/learned/network.py`. One network for the meadow, another for the duel. Each has a bias, a hidden layer of 8 tanh units, and one output score. Meadow weights are `config/policies/wildlife.json`. Duel weights are `config/policies/battle.json`. They are never loaded in place of each other.

**Argmax.** Used whenever Sharp plays: the window, the four-seed tests, and the duel chart. The legal tile with the highest score is chosen. An earlier tile wins a tie.

**Softmax sampling.** Used only while training. The scores become probabilities. One tile is drawn at random from that distribution, so the match explores. The draw, the hidden values, and the probabilities are stored for the update. Play never samples.

**REINFORCE.** `src/application/training.py` for the meadow, `src/application/battle_training.py` for the duel. Used once per training episode, after the match ends. The meadow return is prey killed, minus food eaten, plus 1, 0, or −1 for a hunter win, an unfinished match, or a herd win. The duel return is health the other side lost, minus health the tiger pack lost, plus the same win term. A baseline is 90% of the previous baseline plus 10% of this return. The advantage is the return minus that baseline. Hunter moves are nudged by the advantage. Herd moves are nudged by its opposite. The nudge is spread across every stored move. The learning rate is 0.08. Meadow training was 20 episodes, then 60 more resumed from the saved file, on Riverlands. Duel training was 12 episodes and was not repeated for the jackal roster.

### The five imitators (supervised copies of Wary)

All five live in `src/ai/classical/models.py` and are driven by `src/ai/classical/controller.py`. They are trained by `src/application/classical_training.py` on Wary’s meadow decisions. The saved run is 2 Riverlands matches, 8-round cap, 96 training decisions, 24 held-out decisions. At play they score every legal tile with the meadow feature vector and take the highest score. They are offered in the menu as students of Wary, and they can be selected as the opponent. They do not train on the person’s clicks, and they do not train during a watched match.

**Logistic regression.** One weight per feature and one bias. Training walks the examples for 25 passes. The prediction is a sigmoid of the weighted sum. The weight update is the usual gradient of that sigmoid against the label “this was Wary’s tile” or “it was not.”

**Decision tree.** Grown to depth 3. At each split, candidate cuts on each feature are scored by information gain. A node stops early when it is shallow on examples or the examples already agree. The score of a tile is the fraction of training tiles in its leaf that Wary chose.

**Random forest.** Five trees. Each tree is grown on a sample drawn with replacement, and on 4 features chosen at random, again to depth 3. The tile’s score is the average of the five leaf fractions.

**Naive Bayes.** For the class “Wary chose this tile” and the class “Wary did not,” the model stores the mean and variance of every feature, plus how common each class was. A tile is scored by the log of the Gaussian probability of its features under “chosen,” minus the same quantity under “not chosen.”

**Markov model.** The only imitator with a memory. The situation is coarsened to food or not, a band for enemy distance, a band for influence, and the side. The previous step’s direction is the other half of the state. Training counts how often each direction followed each state. At play, a tile whose direction was common after the previous direction gets the higher count. On the held-out 24 moves this did not beat guessing.

**Holdout check.** Used once, at the end of imitator training. Accuracy is how often the highest-scoring tile is the tile Wary chose, on the last fifth of the recorded moves. Chance is the average of one divided by the number of legal tiles. “Improved” means accuracy is more than two points above that chance.

**Match grade.** `grade_table_play`. Used after the weights are frozen. Each imitator plays both sides of seeds 0–3 for up to 40 rounds. The hunter win count is stored beside the copy score. Fitting is not repeated.

### Duel only

**Scripted fighter.** `src/ai/battle_rules.py`. This is Calm in the duel. On that fighter’s activation it advances toward the other side, attacks when a blow is legal, and holds when the advance does not help.

**Two-ply search.** `src/ai/battle_search.py`. This is Wary in the duel. On that fighter’s activation every legal move and every legal attack is tried on a copy of the board. The copy is scored by expected damage, then by the best reply the visible enemy can make, then by progress and by how much the step drifts. The action with the best key is taken.

**Expected damage.** Inside that search. The blow’s average, reduced when the target stands on a ford. It is an average of the damage range, not a roll. The real roll happens later, in the simulation, if the action is actually played.

**Blind ford filter.** Inside the duel search, and only when no enemy is visible. Ford tiles are removed from the candidate list if any other legal tile exists. Once an enemy is visible, the ford is allowed again.

### Checks that are not training

**Anti-pacing for the five imitators.** `src/ai/classical/controller.py`. Used at play, after the model picks a tile. If that tile is the one the animal just left, the next-best tile is taken instead, unless the reverse step is the one that bites, or it is the richer food tile for a herd animal.

**Sharp’s idle step.** `src/ai/learned/controller.py`. Used at play only. If the network’s best tile is “stay,” no enemy is visible, and the animal is not on food, a herd animal steps toward remembered food and a hunter steps toward unseen ground. Training samples are not changed.

**Obvious bite and obvious flee.** `src/ai/sense.py`. Used at play by Sharp and by the five imitators, after their score and before the action is returned. A hunter who can already reach a bite takes it instead of walking past. A hunter who can see prey and whose chosen tile does not get closer takes a closer legal tile. A herd animal does not stay on, or step onto, a tile beside a ready hunter when another tile is open. Wary does not use this helper. Its own score now counts standing beside a hunter as danger, including the tile the animal is already on. Calm hunters follow A* for their whole movement budget, not a single step.

**Seeded comparison.** `src/application/evaluation.py` and `src/experiments/compare_battle.py`. Used when the charts are built. The same seeds, the same round cap, and the same rules are given to each player. An unfinished match stays unfinished.
