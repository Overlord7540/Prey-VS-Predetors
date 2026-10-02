"""The learned policy trains offline and then acts only on legal tiles."""
import json

from src.ai.learned.controller import LearnedController
from src.application.training import WildlifeTrainer
from src.core.scenario import build_default_scenario


def test_sharp_crosses_the_rookery_at_dusk_instead_of_waiting():
    catalog_match = build_default_scenario(
        seed=1, scenario_name="rookery", start="dusk",
        controllers={
            "predator": LearnedController(),
            "prey": LearnedController(),
        },
    )
    crossed = False
    for _ in range(12):
        catalog_match.step()
        if any(unit.alive and unit.pos[0] >= catalog_match.grid.river_row for unit in catalog_match.predators):
            crossed = True
            break
    assert crossed


def test_same_seed_trains_the_same_weights():
    trainer = WildlifeTrainer()
    first = trainer.run(episodes=1, max_rounds=2, seed=3)
    second = trainer.run(episodes=1, max_rounds=2, seed=3)
    assert first["w1"] == second["w1"]
    assert first["training"]["curve"] == second["training"]["curve"]


def test_trained_policy_picks_a_legal_tile_and_repeats_it():
    record = WildlifeTrainer().run(episodes=1, max_rounds=2, seed=5)
    match = build_default_scenario(seed=5)
    actor = match.prey[0]
    observation = match.observe(actor.agent_id)
    first = LearnedController(weights=record).choose_action(observation)
    second = LearnedController(weights=record).choose_action(observation)
    assert first == second
    assert first.destination in observation.legal_destinations


def test_shipped_weights_load_and_match_the_demo_seed():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    demo = json.loads((root / "config" / "demo.json").read_text(encoding="utf-8"))
    assert demo["controller"] == "learned"
    match = build_default_scenario(seed=demo["seed"], scenario_name=demo["scenario"])
    match.default_controller = LearnedController()
    before = match.turn
    match.step()
    assert match.turn == before + 1
    assert all(reason == "Learned policy" for reason in match.decision_reasons.values())
