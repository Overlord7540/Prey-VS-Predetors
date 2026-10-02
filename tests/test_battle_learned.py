"""The skirmish network trains offline and does not load the wildlife weights."""
import json
from pathlib import Path

import pytest

from src.ai.learned.battle_controller import WEIGHTS_PATH, BattleLearnedController
from src.ai.learned.battle_features import FEATURE_COUNT
from src.ai.learned.controller import LearnedController
from src.application.battle_training import BattleTrainer
from src.core.battle import build_battle
from src.core.battle_match import BattleMatch


def test_same_seed_trains_the_same_battle_weights():
    trainer = BattleTrainer()
    first = trainer.run(episodes=1, max_rounds=1, seed=3)
    second = trainer.run(episodes=1, max_rounds=1, seed=3)
    assert first["domain"] == "battle"
    assert first["n_in"] == FEATURE_COUNT
    assert first["w1"] == second["w1"]
    assert first["training"]["curve"] == second["training"]["curve"]


def test_trained_battle_policy_picks_a_legal_action_and_repeats_it():
    record = BattleTrainer().run(episodes=1, max_rounds=1, seed=5)
    match = BattleMatch(build_battle(), BattleLearnedController(weights=record), seed=5)
    view = match._view(match.fighter("Sable"))
    first = BattleLearnedController(weights=record).choose_action(view)
    second = BattleLearnedController(weights=record).choose_action(view)
    assert first == second
    assert first.destination in view.legal_destinations
    if first.target is not None:
        assert (first.destination, first.target) in view.attacks


def test_battle_weights_are_not_the_wildlife_network():
    wildlife = json.loads(Path("config/policies/wildlife.json").read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="do not match"):
        BattleLearnedController(weights=wildlife)
    with pytest.raises(RuntimeError, match="no trained weights"):
        BattleLearnedController(load_default=False).choose_action(None)


def test_shipped_battle_weights_step_the_skirmish():
    assert WEIGHTS_PATH.name == "battle.json"
    controller = BattleLearnedController()
    assert controller.net.n_in == FEATURE_COUNT
    assert controller.net.n_in != LearnedController().net.n_in
    match = BattleMatch(build_battle(), controller, seed=1, max_rounds=2)
    match.step()
    assert match.events[0]["actor"] == "Sable"
