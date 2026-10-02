"""Slice 4: grass, deer, and tiger are PNG masters scaled by whole numbers."""
import pytest

pygame = pytest.importorskip("pygame")


def test_png_masters_load_at_integer_sizes():
    pygame.init()
    pygame.display.set_mode((1, 1))
    from src.rendering.asset_manager import AssetManager
    from src.rendering.camera import Camera

    assets = AssetManager()
    assert assets.get_sprite("deer", 32, include_label=False).get_size() == (32, 32)
    assert assets.get_sprite("tiger", 64, include_label=False).get_size() == (64, 64)
    assert assets.get_tile("open_field", 32, variant=1).get_size() == (32, 32)
    camera = Camera(4, 4)
    assert camera.tile_size == 64
    camera.zoom()
    assert camera.tile_size == 32
    camera.zoom()
    assert camera.tile_size == 96
    camera.zoom()
    assert camera.tile_size == 64
