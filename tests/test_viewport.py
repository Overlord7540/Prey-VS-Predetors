from src.rendering.viewport import fit_viewport, initial_window_size, window_to_canvas


def test_window_starts_inside_small_desktop():
    width, height = initial_window_size((840, 710), (1024, 600))
    assert width <= 921 and height <= 480


def test_resize_preserves_layout_and_click_coordinates():
    content = (840, 710)
    for window in [(400, 300), (1920, 1080), (300, 800), (840, 710)]:
        x, y, w, h = fit_viewport(content, window)
        assert x >= 0 and y >= 0 and x + w <= window[0] and y + h <= window[1]
        # Center of the Next action button in the logical layout.
        target = (463, 668)
        click = (x + target[0] * w / content[0], y + target[1] * h / content[1])
        mapped = window_to_canvas(click, content, window)
        assert abs(mapped[0] - target[0]) < 0.001
        assert abs(mapped[1] - target[1]) < 0.001


def test_letterbox_clicks_are_ignored():
    assert window_to_canvas((0, 0), (840, 710), (1920, 1080)) is None
