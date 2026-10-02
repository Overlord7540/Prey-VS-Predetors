"""A plain account of one decision: the mind, what it saw, and the step it refused."""
from __future__ import annotations

from dataclasses import dataclass

from src.ai.classical.controller import LABELS


@dataclass(frozen=True)
class Briefing:
    actor_id: str
    mind: str
    seen: str
    step: str
    declined: str


def mind_of(controller) -> str:
    name = getattr(controller, "name", None)
    if name in LABELS:
        return LABELS[name]
    return {
        "RuleBasedController": "Calm",
        "TacticalController": "Wary",
        "LearnedController": "Sharp",
    }.get(type(controller).__name__, type(controller).__name__)


def note_decision(controller, observation, action) -> Briefing:
    actor = observation.actor
    reason = action.reason or (
        "Steps toward the nearest prize." if mind_of(controller) == "Calm" else "Steps to a chosen tile.")
    return Briefing(actor.agent_id, mind_of(controller), _seen(observation), reason, _declined(controller, actor.pos, action.destination))


def _seen(observation) -> str:
    actor = observation.actor
    visible = set(observation.visible)
    enemies = [agent for agent in observation.agents
               if agent.alive and agent.side != actor.side and agent.pos in visible]
    food = sum(1 for pos in visible if observation.grid.resources_remaining.get(pos, 0) > 0)
    if not enemies:
        sight = "No enemy in sight."
    else:
        counts: dict[str, int] = {}
        for agent in enemies:
            counts[agent.species] = counts.get(agent.species, 0) + 1
        parts = [f"{count} {species}" if count > 1 else f"a {species}" for species, count in counts.items()]
        sight = "Sees " + " and ".join(parts) + "."
    if food:
        sight += f" {food} food {'tile is' if food == 1 else 'tiles are'} in sight."
    return sight


def _declined(controller, origin, chosen) -> str:
    other = getattr(controller, "runner_up", None)
    if other is None or other == chosen:
        if type(controller).__name__ == "RuleBasedController":
            return "This mind takes the nearest prize and does not rank a second step."
        return "No other legal step stood out."
    return "Turned down a step " + _toward(origin, other) + "."


def _toward(origin, dest) -> str:
    down, right = dest[0] - origin[0], dest[1] - origin[1]
    if down == 0 and right == 0:
        return "that stays on this tile"
    parts = []
    if down:
        parts.append(f"{abs(down)} {'south' if down > 0 else 'north'}")
    if right:
        parts.append(f"{abs(right)} {'east' if right > 0 else 'west'}")
    return " and ".join(parts)
