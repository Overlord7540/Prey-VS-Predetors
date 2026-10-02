"""Map-only camera; zoom never changes sidebar size or simulation coordinates."""
import math

# 32 fits a 20×20 board in the 960×720 view. 64 and 96 are closer.
ZOOM_SIZES = (64, 32, 96)


class Camera:
    def __init__(self, columns, rows, viewport=(960, 720), tile_size=64):
        self.columns, self.rows = columns, rows
        self.width, self.height = viewport
        self.tile_size = tile_size
        self.x = self.y = 0
        self._target = None

    def pan(self, dx, dy):
        if dx or dy:
            self._target = None
        self.x = max(0, min(self.x + dx, max(0, self.columns*self.tile_size-self.width)))
        self.y = max(0, min(self.y + dy, max(0, self.rows*self.tile_size-self.height)))

    def zoom(self):
        cx = (self.x+self.width/2)/self.tile_size
        cy = (self.y+self.height/2)/self.tile_size
        current = ZOOM_SIZES.index(self.tile_size) if self.tile_size in ZOOM_SIZES else 0
        self.tile_size = ZOOM_SIZES[(current + 1) % len(ZOOM_SIZES)]
        self._target = None
        self.x = round(cx*self.tile_size-self.width/2)
        self.y = round(cy*self.tile_size-self.height/2)
        self.pan(0, 0)

    def origin(self):
        """Inset the board when it fits; zoomed maps stay pinned for panning."""
        world_w = self.columns * self.tile_size
        world_h = self.rows * self.tile_size
        x = (self.width - world_w) // 2 if world_w < self.width else 0
        y = (self.height - world_h) // 2 if world_h < self.height else 0
        return x, y

    def tile_at(self, point):
        if point is None or not (0 <= point[0] < self.width and 0 <= point[1] < self.height):
            return None
        ox, oy = self.origin()
        tile = (int((point[1] - oy + self.y) // self.tile_size),
                int((point[0] - ox + self.x) // self.tile_size))
        return tile if 0 <= tile[0] < self.rows and 0 <= tile[1] < self.columns else None

    def _clamped(self, tile):
        x = round((tile[1] + .5) * self.tile_size - self.width / 2)
        y = round((tile[0] + .5) * self.tile_size - self.height / 2)
        max_x = max(0, self.columns * self.tile_size - self.width)
        max_y = max(0, self.rows * self.tile_size - self.height)
        return max(0, min(x, max_x)), max(0, min(y, max_y))

    def focus(self, tile):
        self.x, self.y = self._clamped(tile)
        self._target = None

    def glance(self, tile):
        """Ease toward the animal that is acting. A board that already fits stays put."""
        target = self._clamped(tile)
        self._target = None if target == (self.x, self.y) else target

    def follow(self, dt):
        if not self._target or dt <= 0:
            return
        tx, ty = self._target
        blend = 1 - math.exp(-7 * dt)
        self.x = self._ease(self.x, tx, blend)
        self.y = self._ease(self.y, ty, blend)
        if abs(self.x - tx) <= 1 and abs(self.y - ty) <= 1:
            self.x, self.y = tx, ty
            self._target = None

    @staticmethod
    def _ease(current, target, blend):
        delta = target - current
        moved = round(delta * blend)
        if moved == 0 and delta:
            moved = 1 if delta > 0 else -1
        return current + moved
