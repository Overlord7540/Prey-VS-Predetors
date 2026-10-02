"""Search keeps the blow that survives the visible counterattack."""
from src.ai.battle_rules import RuleBattleController
from src.ai.battle_search import SearchBattleController
from src.core.battle import build_battle
from src.core.battle_match import BattleMatch


def _punished_view():
    match = BattleMatch(build_battle(), RuleBattleController(), seed=1)
    sable = match.fighter("Sable")
    fern = match.fighter("Cinder")
    moss = match.fighter("Nettle")
    sable.pos = (4, 6)
    fern.pos = (4, 7)
    fern.move_range = 0
    moss.pos = (3, 6)
    moss.move_range = 0
    moss.damage = 40
    moss.damage_spread = 0
    match.fighter("Bramble").alive = False
    return match._view(sable)


def test_search_steps_onto_the_ford_instead_of_taking_the_punished_blow():
    view = _punished_view()
    rule = RuleBattleController().choose_action(view)
    search = SearchBattleController().choose_action(view)
    assert rule.destination == (4, 6) and rule.target == "Cinder"
    assert search.destination == (5, 6) and search.target == "Cinder"
    assert search.reason == "Search"
    assert SearchBattleController().choose_action(view) == search


def test_search_stays_off_the_ford_until_it_can_see_an_enemy():
    controllers = {"hunter": SearchBattleController(), "herd": RuleBattleController()}
    match = BattleMatch(build_battle(), controllers, seed=0)
    for _ in range(3):
        match.step()
    for name in ("Sable", "Ash", "Birch"):
        row, col = match.fighter(name).pos
        assert match.grid.tiles[row][col] != "chokepoint"


def test_search_can_play_one_side_of_a_skirmish():
    controllers = {"hunter": SearchBattleController(), "herd": RuleBattleController()}
    match = BattleMatch(build_battle(), controllers, seed=1, max_rounds=2)
    for _ in range(6):
        match.step()
    assert match.round == 1
    assert any(event["actor"] == "Sable" for event in match.events)
