"""The skirmish roster and map. Wildlife scenarios stay herd matches."""
import pytest

from src.core.battle import build_battle
from src.core.scenario import build_default_scenario
from src.data.loader import load_named_scenario


def test_skirmish_is_a_tiger_pack_against_three_jackals():
    battle = build_battle()
    assert battle.grid.width == 12 and battle.grid.height == 10
    assert battle.grid.river_row == 5
    assert battle.grid.resources_remaining == {}
    ford = [(5, 5), (5, 6)]
    assert all(battle.grid.tiles[row][col] == "chokepoint" for row, col in ford)
    assert all(battle.grid.is_passable(pos) for pos in ford)
    assert battle.grid.tile_props((3, 1)).blocks_los
    assert not battle.grid.is_passable((3, 1))

    hunters = battle.side("hunter")
    herd = battle.side("herd")
    assert [fighter.name for fighter in hunters] == ["Sable", "Ash", "Birch"]
    assert [fighter.name for fighter in herd] == ["Cinder", "Nettle", "Bramble"]
    assert [fighter.body for fighter in hunters] == ["tiger", "wolf", "wolf"]
    assert [fighter.body for fighter in herd] == ["jackal", "jackal", "jackal"]
    sable, ash, birch = hunters
    cinder, nettle, bramble = herd
    assert (sable.hp, sable.move_range, sable.damage, sable.damage_spread) == (48, 3, 32, 10)
    assert (ash.hp, ash.move_range, ash.damage, ash.damage_spread) == (36, 4, 22, 6)
    assert birch.hp == ash.hp and birch.damage == ash.damage
    assert (cinder.hp, cinder.move_range, cinder.damage, cinder.damage_spread) == (36, 4, 20, 6)
    assert (nettle.hp, nettle.move_range, nettle.damage) == (36, 4, 20)
    assert (bramble.hp, bramble.move_range, bramble.damage, bramble.damage_spread) == (42, 3, 22, 6)
    for fighter in hunters:
        assert fighter.pos[0] < battle.grid.river_row
        assert battle.grid.is_passable(fighter.pos)
    for fighter in herd:
        assert fighter.pos[0] > battle.grid.river_row
        assert battle.grid.is_passable(fighter.pos)


def test_wildlife_scenarios_do_not_load_the_battle():
    classic = build_default_scenario(seed=1)
    assert {prey.species for prey in classic.prey} == {"deer"}
    with pytest.raises(ValueError, match="Unknown scenario"):
        load_named_scenario("skirmish")
    with pytest.raises(ValueError, match="Unknown battle"):
        build_battle("missing")
