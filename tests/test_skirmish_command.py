"""A person can order one side of the skirmish. The other side keeps its controller."""
import pytest

from src.core.control import Action
from src.rendering.skirmish import SkirmishMatch


def test_the_human_side_does_not_move_until_ordered():
    match = SkirmishMatch("rules", 1, "hunter")
    start = match.battle.fighter("Sable").pos
    assert match.human_turn and match.pending_player_ids == {"Sable"}
    assert match.phase.startswith("Sable")
    match.step()
    assert match.battle.fighter("Sable").pos == start
    destination = next(tile for tile in match.observe("Sable").legal_destinations if tile[0] > start[0])
    match.submit_player_action("Sable", Action(destination, kind="wait"))
    assert match.battle.fighter("Sable").pos == destination
    assert match.pending_player_ids == {"Ash"}


def test_a_commanded_blow_lands_and_a_bad_tile_is_refused():
    match = SkirmishMatch("rules", 1, "hunter")
    match.battle.fighter("Sable").pos = (4, 6)
    match.battle.fighter("Cinder").pos = (4, 7)
    with pytest.raises(ValueError, match="highlighted"):
        match.submit_player_action("Sable", Action((0, 0), kind="wait"))
    before = match.battle.fighter("Cinder").hp
    match.submit_player_action("Sable", Action((4, 6), kind="attack", target_id="Cinder"))
    assert match.battle.fighter("Cinder").hp < before


def test_the_jackal_player_waits_while_the_tiger_pack_is_the_opponent():
    match = SkirmishMatch("rules", 1, "herd")
    assert not match.human_turn
    for _ in range(3):
        match.step()
    assert match.human_turn and match.pending_player_ids == {"Cinder"}
