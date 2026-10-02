"""Cross-play the three skirmish controllers on shared seeds. Charts stay outside."""
from __future__ import annotations

from src.ai.battle_rules import RuleBattleController
from src.ai.battle_search import SearchBattleController
from src.ai.learned.battle_controller import BattleLearnedController
from src.core.battle import build_battle
from src.core.battle_match import BattleMatch

NAMES = ("rules", "search", "learned")


class BattleEvaluation:
    def __init__(self) -> None:
        self._factories = {
            "rules": RuleBattleController,
            "search": SearchBattleController,
            "learned": BattleLearnedController,
        }

    def compare(self, start_seed: int = 0, matches: int = 4, max_rounds: int = 8) -> dict:
        if matches < 1 or max_rounds < 1:
            raise ValueError("matches and max_rounds must be positive")
        games = []
        for seed in range(start_seed, start_seed + matches):
            for hunter in NAMES:
                for herd in NAMES:
                    if hunter == herd:
                        continue
                    games.append(self._play(hunter, herd, seed, max_rounds))
        return {
            "start_seed": start_seed,
            "matches": matches,
            "max_rounds": max_rounds,
            "controllers": [self._tally(name, games) for name in NAMES],
            "games": games,
        }

    def _play(self, hunter: str, herd: str, seed: int, max_rounds: int) -> dict:
        match = BattleMatch(
            build_battle(),
            {"hunter": self._factories[hunter](), "herd": self._factories[herd]()},
            seed=seed,
            max_rounds=max_rounds,
        )
        steps = 0
        while not match.finished and steps < max_rounds * 8:
            match.step()
            steps += 1
        return {
            "seed": seed,
            "hunter": hunter,
            "herd": herd,
            "winner": match.winner,
            "rounds": match.round,
            "hunter_hp": _health(match, "hunter"),
            "herd_hp": _health(match, "herd"),
        }

    def _tally(self, name: str, games: list[dict]) -> dict:
        wins = losses = unfinished = 0
        own = opponent = 0.0
        played = []
        for game in games:
            if game["hunter"] == name:
                side, other = "hunter", "herd"
            elif game["herd"] == name:
                side, other = "herd", "hunter"
            else:
                continue
            played.append(game)
            if game["winner"] is None:
                unfinished += 1
            elif game["winner"] == side:
                wins += 1
            else:
                losses += 1
            own += game[f"{side}_hp"]
            opponent += game[f"{other}_hp"]
        count = max(1, len(played))
        return {
            "name": name,
            "outcomes": {"wins": wins, "losses": losses, "unfinished": unfinished},
            "mean_own_hp": own / count,
            "mean_opponent_hp": opponent / count,
            "matches": played,
        }


def _health(match: BattleMatch, side: str) -> int:
    return sum(unit.hp for unit in match.combatants if unit.side == side and unit.alive)
