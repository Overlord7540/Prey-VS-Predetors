"""Rules, search, and the battle network meet on the same seeds."""
from src.adapters.reports.charts import ComparisonChartReport
from src.application.battle_evaluation import BattleEvaluation


def test_each_controller_plays_both_sides_against_the_other_two():
    comparison = BattleEvaluation().compare(start_seed=0, matches=1, max_rounds=2)
    assert [row["name"] for row in comparison["controllers"]] == ["rules", "search", "learned"]
    assert all(game["hunter"] != game["herd"] for game in comparison["games"])
    for row in comparison["controllers"]:
        outcomes = row["outcomes"]
        assert sum(outcomes.values()) == 4
        assert len(row["matches"]) == 4


def test_battle_charts_write_without_running_a_match(tmp_path):
    comparison = {
        "controllers": [
            {"name": "rules", "outcomes": {"wins": 1, "losses": 2, "unfinished": 1},
             "mean_own_hp": 30, "mean_opponent_hp": 40},
            {"name": "search", "outcomes": {"wins": 3, "losses": 1, "unfinished": 0},
             "mean_own_hp": 50, "mean_opponent_hp": 20},
        ]
    }
    report = ComparisonChartReport()
    wins = report.write_battle_outcomes(comparison, tmp_path / "wins.png")
    health = report.write_battle_health(comparison, tmp_path / "health.png")
    assert wins.stat().st_size > 0
    assert health.stat().st_size > 0
