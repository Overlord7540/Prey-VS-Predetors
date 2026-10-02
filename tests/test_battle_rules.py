"""A skirmish steps move-then-act. Wildlife matches stay on their own rules."""
from src.ai.battle_rules import RuleBattleController
from src.core.battle import build_battle
from src.core.battle_match import BattleAction, BattleMatch
from src.core.scenario import build_default_scenario


class _Script:
    def __init__(self, action):
        self.action = action
        self.views = []

    def choose_action(self, view):
        self.views.append(view)
        return self.action


def _attack_damage(defender_pos, seed=1):
    script = _Script(BattleAction((4, 5), "Bramble", "test"))
    match = BattleMatch(build_battle(), script, seed=seed)
    match.fighter("Sable").pos = (4, 5)
    match.fighter("Bramble").pos = defender_pos
    match.step()
    return next(event["damage"] for event in match.events if event["kind"] == "attack")


def test_rule_controller_advances_then_the_sides_trade_blows():
    match = BattleMatch(build_battle(), RuleBattleController(), seed=1, max_rounds=8)
    match.step()
    assert match.fighter("Sable").pos[0] > 1
    assert not any(event["kind"] == "attack" for event in match.events)
    while not match.finished:
        match.step()
    assert any(event["kind"] == "attack" for event in match.events)
    assert match.winner in ("hunter", "herd")


def test_cover_reduces_one_chosen_blow_and_movement_does_not_strike():
    covered = _attack_damage((5, 5))
    opened = _attack_damage((4, 6))
    assert covered == max(1, opened - 4)

    script = _Script(BattleAction((4, 5), "Bramble", "walk"))
    match = BattleMatch(build_battle(), script, seed=3)
    match.fighter("Sable").pos = (2, 5)
    match.fighter("Bramble").pos = (6, 5)
    match.step()
    assert match.fighter("Sable").pos == (4, 5)
    assert match.fighter("Bramble").hp == 42
    assert not any(event["kind"] == "attack" for event in match.events)


def test_a_fighter_cannot_strike_or_name_an_enemy_hidden_by_rock():
    script = _Script(BattleAction((2, 1), "Cinder", "test"))
    match = BattleMatch(build_battle(), script, seed=1)
    sable = match.fighter("Sable")
    sable.pos = (2, 1)
    sable.move_range = 0
    match.fighter("Cinder").pos = (4, 1)
    match.step()
    assert "Cinder" not in {enemy.name for enemy in script.views[0].enemies}
    assert script.views[0].attacks == ()
    assert match.fighter("Cinder").hp == 36


def test_wildlife_match_still_steps_on_its_own_rules():
    match = build_default_scenario(seed=1)
    match.step()
    assert match.turn == 1
    assert {prey.species for prey in match.prey} == {"deer"}
