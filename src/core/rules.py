"""Validated match rules shared by simulation, perception, and controllers."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Rules:
    predator_win_prey_elimination_pct: float = 0.70
    prey_win_resource_pool_pct: float = 0.65
    panic_detection_range: int = 6
    despair_recovery_range: int = 3
    sight_range: int = 6

    def __post_init__(self):
        for value in (self.predator_win_prey_elimination_pct, self.prey_win_resource_pool_pct):
            if not 0 < value <= 1:
                raise ValueError("Victory thresholds must be in (0, 1]")
        for value in (self.panic_detection_range, self.despair_recovery_range, self.sight_range):
            if type(value) is not int or value < 0:
                raise ValueError("Detection/recovery ranges must be nonnegative integers")
