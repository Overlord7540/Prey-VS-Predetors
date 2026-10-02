"""Shared scheduler: human input pauses both detailed and fast playback."""


def round_sequence(sim):
    sim.turn += 1
    sim._begin_combat_round()
    for side, agents, execute in (
        ("predator", sim.predators, sim._act_predator),
        ("prey", sim.prey, sim._act_prey),
    ):
        sim.phase = "Predator turn" if side == "predator" else "Prey turn"
        sim.active_agent_id = None
        sim.last_action = None
        if side == "prey":
            sim._tick_flocks()
        human = sim.player_side == side
        if human:
            sim.pending_player_ids = {a.agent_id for a in agents if a.alive}
            sim.human_turn = True
        yield
        if not human:
            for agent in agents:
                if agent.alive:
                    sim._show_action(agent, execute)
                    yield
    sim._check_win_conditions()
    sim._log_turn()
    sim.phase = "Round complete"
    sim.active_agent_id = None
    sim.last_action = None
    yield
