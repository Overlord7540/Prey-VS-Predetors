"""Slice 2: controller, training, and report boundaries do not change match rules."""
from pathlib import Path

from src.adapters.persistence.result_store import ResultStore
from src.adapters.pygame_ui.boundary import PygameUI
from src.adapters.reports.charts import ComparisonChartReport
from src.ai.baselines import RuleBasedController
from src.ai.catalog import wildlife_catalog
from src.ai.learned.controller import LearnedController
from src.ai.tactical import TacticalController
from src.application.evaluation import BatchEvaluation
from src.experiments.run import run_batch


ROOT = Path(__file__).resolve().parents[1]


def test_catalog_exposes_playable_wildlife_controllers_only():
    catalog = wildlife_catalog()
    assert catalog.playable_names() == (
        "baseline", "tactical", "learned", "logistic", "tree", "forest", "bayes", "markov",
    )
    assert isinstance(catalog.create("baseline"), RuleBasedController)
    assert isinstance(catalog.create("tactical"), TacticalController)
    assert isinstance(catalog.create("learned"), LearnedController)


def test_untrained_learned_controller_refuses_to_act():
    try:
        LearnedController(load_default=False).choose_action(None)
    except RuntimeError as error:
        assert "no trained weights" in str(error)
    else:
        raise AssertionError("Untrained controller returned an action")


def test_batch_entry_points_match():
    direct = BatchEvaluation().run(start_seed=5, matches=1, max_rounds=1, controller="baseline")
    wrapped = run_batch(start_seed=5, matches=1, max_rounds=1, controller="baseline")
    assert direct == wrapped
    assert direct["controller"] == "RuleBasedController"


def test_result_store_round_trip(tmp_path):
    record = {"outcomes": {"unfinished": 1}, "matches": []}
    path = tmp_path / "batch.json"
    ResultStore().save(record, path)
    assert ResultStore().load(path) == record


def test_chart_report_writes_figures(tmp_path):
    report = ComparisonChartReport()
    wins = report.write_win_rates({"controller": "demo", "outcomes": {"predator": 2, "prey": 1}},
                                   tmp_path / "wins.png")
    curve = report.write_training_curve([1.0, 0.5, 0.2], tmp_path / "curve.png")
    assert wins.stat().st_size > 0
    assert curve.stat().st_size > 0


def test_pygame_boundary_does_not_import_pygame_at_module_level():
    source = (ROOT / "src" / "adapters" / "pygame_ui" / "boundary.py").read_text(encoding="utf-8")
    assert "import pygame" not in source.split("def load")[0]
    assert PygameUI().load


def test_inner_packages_do_not_import_pygame_or_matplotlib():
    for folder in ("core", "ai", "application"):
        for path in (ROOT / "src" / folder).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "import pygame" not in text and "from pygame" not in text, path
            assert "matplotlib" not in text, path
