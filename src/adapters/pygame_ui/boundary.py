"""Loads the current display types without importing pygame at module import."""
from __future__ import annotations


class PygameUI:
    def load(self) -> dict:
        from src.rendering.asset_manager import AssetManager
        from src.rendering.renderer import Renderer, TILE_SIZE
        return {"AssetManager": AssetManager, "Renderer": Renderer, "TILE_SIZE": TILE_SIZE}
