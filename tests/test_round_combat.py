import random
import pytest
from tests.support import make_sim, fixed_move
from src.core.agent import PredatorAgent, PredatorIntent, PreyState
from src.core.control import Action


def test_tiger_cannot_attack_twice_in_round():
    tiger = PredatorAgent('t', 'tiger', (0, 0), 'predator', intent=PredatorIntent.CHASE)
    sim = make_sim([(0, 1), (1, 0), (9, 11)], tiger)
    sim._predator_turn()
    assert sum(event.kind == "hit" for event in sim.events) == 1 and tiger.attack_used
    assert sim.prey[0].alive and sim.grid.chebyshev_distance(tiger.pos, sim.prey[0].pos) > 1
    assert not sim._attack(tiger, sim.prey[1])


def test_movement_does_not_trigger_automatic_attacks():
    tiger = PredatorAgent('t', 'tiger', (0, 0), 'predator')
    sim = make_sim([(0, 2)], tiger)
    with fixed_move(sim, (0, 1)):
        sim._act_prey(sim.prey[0])
    assert sim.prey[0].hp == 40 and not tiger.attack_used
    assert sim.grid.resources_remaining[(0, 1)] == 0


def test_survivor_gets_one_escape_activation_and_cooldown():
    wolf = PredatorAgent('w', 'wolf', (0, 0), 'predator')
    second = PredatorAgent('w2', 'wolf', (0, 2), 'predator')
    sim = make_sim([(0, 1)], wolf)
    sim.predators.append(second)
    victim = sim.prey[0]
    victim.hp = victim.max_hp = 100
    assert sim._attack(wolf, victim)
    assert victim.state == PreyState.DESPAIR
    assert victim.adrenaline and victim.escape_guard
    assert sim.grid.chebyshev_distance(wolf.pos, victim.pos) > 1
    assert not sim._attack(second, victim)
    sim._act_prey(victim, Action(victim.pos, kind='wait'))
    assert not victim.adrenaline and not victim.escape_guard
    assert victim.adrenaline_cooldown == 2
    victim.pos = (0, 1)
    assert sim._attack(second, victim)
    assert not victim.adrenaline


def test_wolf_kill_cooldown_blocks_next_round():
    wolf = PredatorAgent('w', 'wolf', (0, 0), 'predator')
    sim = make_sim([(0, 1), (1, 0)], wolf)
    sim.prey[0].hp = 1
    assert sim._attack(wolf, sim.prey[0])
    assert wolf.cooldown_remaining == 1
    sim._begin_combat_round()
    assert not sim._attack(wolf, sim.prey[1])
    sim._begin_combat_round()
    assert sim._attack(wolf, sim.prey[1])


def test_preview_is_pure_and_roll_is_bounded_and_repeatable():
    damages = []
    for seed in range(30):
        tiger = PredatorAgent('t', 'tiger', (0, 0), 'predator')
        sim = make_sim([(0, 1)], tiger)
        sim.rng = random.Random(seed)
        state = sim.rng.getstate()
        assert sim.attack_preview('t', '0', tiger.pos) == (22, 39, 1, 18)
        assert sim.rng.getstate() == state
        assert sim._attack(tiger, sim.prey[0])
        expected = min(39, random.Random(seed).randint(22, 42))
        assert sim.events[0].damage == expected and sim.prey[0].alive
        damages.append(expected)
    assert len(set(damages)) > 1 and 40 not in damages and min(damages) < 40


def test_explicit_target_validation_preserves_action_and_rng():
    tiger = PredatorAgent('t', 'tiger', (0, 0), 'predator')
    sim = make_sim([(0, 1), (9, 11)], tiger)
    sim.player_side = 'predator'
    sim.step()
    before = sim.rng.getstate()
    with pytest.raises(ValueError):
        sim.submit_player_action('t', Action((0, 0), kind='attack', target_id='1'))
    assert sim.rng.getstate() == before and 't' in sim.pending_player_ids
    sim.submit_player_action('t', Action((0, 0), kind='attack', target_id='0'))
    assert sim.prey[1].hp == 40 and sim.prey[0].hp < 40
    assert 't' not in sim.pending_player_ids
