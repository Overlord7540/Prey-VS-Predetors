"""Aspect-preserving window layout and mouse mapping (no Pygame required)."""


def fit_viewport(content_size, window_size):
    width, height = content_size
    available_w, available_h = window_size
    scale = min(max(1, available_w) / width, max(1, available_h) / height)
    fitted_w = max(1, min(available_w, int(width * scale)))
    fitted_h = max(1, min(available_h, int(height * scale)))
    return ((available_w - fitted_w) // 2, (available_h - fitted_h) // 2,
            fitted_w, fitted_h)


def window_to_canvas(position, content_size, window_size):
    left, top, width, height = fit_viewport(content_size, window_size)
    x, y = position
    if not (left <= x < left + width and top <= y < top + height):
        return None
    return ((x - left) * content_size[0] / width,
            (y - top) * content_size[1] / height)


def initial_window_size(content_size, desktop_size):
    # Leave room for the taskbar, title bar, and window borders.
    available = (max(1, int(desktop_size[0] * 0.9)),
                 max(1, int(desktop_size[1] * 0.8)))
    bounds = (min(content_size[0], available[0]), min(content_size[1], available[1]))
    return fit_viewport(content_size, bounds)[2:]
