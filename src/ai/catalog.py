"""Named wildlife controllers. Application code asks the catalog, not individual modules."""
from __future__ import annotations

from src.ai.classical.controller import LABELS, TableController
from src.ai.learned.controller import LearnedController
from src.ai.policies import RuleBasedController, TacticalController

PLAYER_LABELS = {
    "baseline": "Greedy",
    "tactical": "Tactical",
    "learned": "Neural policy",
    **LABELS,
}


class ControllerCatalog:
    def __init__(self) -> None:
        self._types: dict[str, type] = {}

    def register(self, name: str, controller_type: type) -> None:
        if name in self._types:
            raise ValueError(f"Controller already registered: {name}")
        self._types[name] = controller_type

    def create(self, name: str):
        try:
            controller_type = self._types[name]
        except KeyError:
            raise ValueError("Unknown controller") from None
        controller = controller_type()
        if not getattr(controller, "playable", True):
            raise ValueError("Controller is not playable")
        return controller

    def playable_names(self) -> tuple[str, ...]:
        return tuple(name for name, controller_type in self._types.items()
                     if getattr(controller_type(), "playable", True))


def wildlife_catalog() -> ControllerCatalog:
    catalog = ControllerCatalog()
    catalog.register("baseline", RuleBasedController)
    catalog.register("tactical", TacticalController)
    catalog.register("learned", LearnedController)
    for name in LABELS:
        catalog.register(name, _table(name))
    return catalog


def _table(name: str):
    class _Bound(TableController):
        def __init__(self) -> None:
            super().__init__(name)
    _Bound.__name__ = f"{name.title()}Controller"
    return _Bound
