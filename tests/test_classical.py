"""Table players copy Tactical, and the report says whether that beat guessing."""
from src.ai.catalog import wildlife_catalog
from src.ai.classical.controller import TableController
from src.application.classical_training import measure_table_players, training_lines
from src.rendering.menu import menu_choices


def _obvious_samples(count=40):
    chosen = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    other = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    return [([chosen, other], 0) for _ in range(count)]


def test_logistic_beats_guessing_when_the_label_is_obvious():
    record = measure_table_players(_obvious_samples(), seed=1)
    logistic = record["models"]["logistic"]
    assert logistic["test_accuracy"] > logistic["chance"]
    assert logistic["improved"] is True


def test_report_names_the_three_players_and_says_whether_each_model_improved():
    record = measure_table_players(_obvious_samples(), seed=1)
    record.update({"matches": 1, "max_rounds": 1})
    lines = " ".join(training_lines(record))
    assert "Greedy" in lines and "Tactical" in lines and "Neural policy" in lines
    assert "better than guessing" in lines
    assert "Logistic regression" in lines and "Markov model" in lines


def test_logistic_does_not_pace_between_two_tiles_on_the_glade():
    from src.core.scenario import build_default_scenario
    catalog = wildlife_catalog()
    sim = build_default_scenario(
        seed=1, scenario_name="glade", start="noon",
        controllers={"predator": catalog.create("logistic"), "prey": catalog.create("logistic")},
    )
    positions = []
    for _ in range(8):
        sim.step()
        positions.append(sim.predators[0].pos)
    shuttles = [
        index for index in range(len(positions) - 3)
        if positions[index] == positions[index + 2]
        and positions[index + 1] == positions[index + 3]
        and positions[index] != positions[index + 1]
    ]
    assert not shuttles


def test_catalog_offers_the_five_table_players():
    names = wildlife_catalog().playable_names()
    assert names[:3] == ("baseline", "tactical", "learned")
    assert names[3:] == ("logistic", "tree", "forest", "bayes", "markov")
    controller = wildlife_catalog().create("logistic")
    assert isinstance(controller, TableController)


def test_untrained_table_player_says_so(tmp_path, monkeypatch):
    from src.ai.classical import controller as module
    monkeypatch.setattr(module, "RECORD_PATH", tmp_path / "missing.json")

    class _View:
        class actor:
            pos = (1, 1)
        legal_destinations = ((1, 1),)

    action = TableController("tree").choose_action(_View())
    assert "not trained yet" in action.reason


def test_classical_menu_lists_the_five_models():
    labels = [label for _key, label in menu_choices("classical")]
    assert labels[:5] == [
        "Logistic regression", "Decision tree", "Random forest", "Naive Bayes", "Markov model",
    ]
    assert [label for _key, label in menu_choices("face")][:3] == ["Calm", "Wary", "Sharp"]
    assert [label for _key, label in menu_choices("home")][:2] == ["New game", "Field notes"]
