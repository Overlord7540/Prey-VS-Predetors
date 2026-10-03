"""Stable display names and inspection text, independent of Pygame."""
from collections import Counter


def build_labels(agents):
    counts = Counter()
    labels = {}
    for agent in agents:
        counts[agent.species] += 1
        labels[agent.agent_id] = f"{agent.species[0].upper()}{counts[agent.species]}"
    return labels


def describe_agent(agent, label):
    if getattr(agent, "battle_name", None):
        pack = "tiger pack" if agent.battle_side == "hunter" else "jackals"
        return [f"{agent.battle_name} ({pack})",
                f"{agent.species.capitalize()}",
                f"HP: {agent.hp}/{agent.max_hp}"]
    lines = [f"{label} - {agent.species.capitalize()} ({agent.side})",
             f"ID: {agent.agent_id}"]
    if agent.side == "prey":
        lines += [f"HP: {agent.hp}/{agent.max_hp}",
                  f"State: {agent.state.name.title()}", f"Herd: {agent.flock_id or 'None'}"]
    else:
        intent = "Chase" if agent.is_constant_chase else (agent.intent.name.title() if agent.intent else "None")
        lines += ["HP: not used for predators", f"Intent: {intent}",
                  f"Attack cooldown: {agent.cooldown_remaining}",
                  "Attack: " + ("resting this round" if agent.resting_this_round else "used this round" if agent.attack_used else "ready"),
                  f"Pack: {agent.pack_id or 'None (independent)'}"]
    return lines


def result_notice(sim) -> tuple[str, str] | None:
    """Victory or defeat for the side being played. A watched match names the winner."""
    winner = getattr(sim, "winner", None)
    if not winner:
        return None
    if getattr(sim, "kind", "") == "skirmish":
        yours = {"predator": "hunter", "prey": "herd"}.get(getattr(sim, "player_side", None))
        detail = "The other side is cleared."
        if yours == winner:
            return "Victory", detail
        if yours:
            return "Defeat", detail
        return ("Tiger pack wins" if winner == "hunter" else "Jackals win"), detail
    detail = "The herd is broken." if winner == "predator" else "The herd ate enough."
    yours = getattr(sim, "player_side", None)
    if yours == winner:
        return "Victory", detail
    if yours:
        return "Defeat", detail
    return ("Hunters win" if winner == "predator" else "The herd wins"), detail


def action_caption(sim, labels):
    record = sim.last_action
    if record is None:
        if sim.winner:
            return f"{sim.winner.capitalize()} wins!"
        return {"Ready": "Predators act first. Start the next round.",
                "Predator turn": "Predators move and attack.",
                "Prey turn": "Prey move and feed.",
                "Round complete": "Both sides have acted. Next: predators."}.get(sim.phase, "")
    movement = (f"moved {record.before} -> {record.after}"
                if record.before != record.after else "held position")
    detail = f"; ate {record.food_consumed} food" if record.food_consumed else ""
    if record.side == "prey" and record.damage:
        detail += "; killed by reaction" if not record.alive else f"; took {record.damage} damage"
    elif record.kills:
        detail += f"; killed {record.kills} prey"
    elif record.damage:
        detail += f"; dealt {record.damage} damage"
    state = ""
    if record.state_before:
        state = (f"[{record.state_before} -> {record.state_after}] "
                 if record.state_before != record.state_after else f"[{record.state_after}] ")
    return f"{labels.get(record.actor, record.actor)}: {state}{movement}{detail}"
