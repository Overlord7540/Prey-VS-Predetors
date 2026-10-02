"""Top-down 16px animals for the Sprout Lands meadow. Edit this file and rerun."""
import sys
from pathlib import Path

sys.path.insert(0, r"C:/Users/Fardin/.codex/skills/pixel-art-studio/scripts")
from pixelstudio import Sprite

OUT = Path(__file__).resolve().parent

# Purple outline matches the Sprout Lands characters, so the animals sit on that grass.
COLORS = {
    "o": "#5c4e92",
    "e": "#3f3568",
    "k": "#e8b5ac",
    "c": "#f3f2c0",
    "h": "#f3e7c4",
    "s": "#8a7848",
    "1": "#a86e42",
    "2": "#c48a55",
    "3": "#e7c39a",
    "4": "#c47a32",
    "5": "#e39a45",
    "6": "#f6d7a4",
    "7": "#6b3f28",
    "8": "#6e6a88",
    "9": "#9a96b0",
    "0": "#ddd8ea",
    "a": "#5c3d30",
    "b": "#7a5340",
    "d": "#b56a28",
    "f": "#e6c15a",
    "g": "#f6e2a2",
}

DEER = [
    "...h......h.....",
    "..hh......hh....",
    "...hho....ohh...",
    ".....o3333o.....",
    "....o3e33e3o....",
    ".....o3333o.....",
    "....o222222o....",
    "...o22211222o...",
    "...o22122212o...",
    "....o2.22.2o....",
    "....o..oo..o....",
    "......ssss......",
    "................",
    "................",
    "................",
    "................",
]

TIGER = [
    "................",
    ".....oo..oo.....",
    "....o66oo66o....",
    "....o6e66e6o....",
    ".....o6666o.....",
    "...o55555555o...",
    "..o7755575557o..",
    "..o5557757755o..",
    "...o55755575o...",
    "....o5.55.5o....",
    "....o..oo..o77..",
    "......ssss..o7o.",
    ".............o..",
    "................",
    "................",
    "................",
]

WOLF = [
    "................",
    "...oo......oo...",
    "..o0o......o0o..",
    "..o0o......o0o..",
    "...oe0.kk.0eo...",
    "....o000000o....",
    "...o99999999o...",
    "..o9988899999o..",
    "..o99.999.99.o..",
    "...o..o...o..o..",
    "..00o..ssss.....",
    ".o0o............",
    "..o.............",
    "................",
    "................",
    "................",
]

BUFFALO = [
    "................",
    "..hh........hh..",
    ".ohh..oooo..hho.",
    "..o..obbbbbo..o.",
    "....obkeekbo....",
    "...obbbbbbbbbo..",
    "..obbbbbbbbbbbo.",
    "..obbbaabbbbbbo.",
    "..obbb.bb.bbbbo.",
    "...o...o...o....",
    "...o...o...o....",
    "....ss.ss.ss....",
    "................",
    "................",
    "................",
    "................",
]

GIRAFFE = [
    "....h......h....",
    "...oho....oho...",
    "....oggeeggo....",
    "...oggggggo.....",
    "....offffo......",
    "....ofdffo......",
    "....offffo......",
    "....ofddfo......",
    "...offffffo.....",
    "...ofdffdfo.....",
    "..off.ff.ffo....",
    "...o..oo..o.....",
    "....ss..ss......",
    "................",
    "................",
    "................",
]


def draw(rows):
    if any(len(row) != 16 for row in rows) or len(rows) != 16:
        raise ValueError("every animal is a 16 by 16 grid")
    sprite = Sprite(16, 16)
    for y, row in enumerate(rows):
        for x, mark in enumerate(row):
            if mark != ".":
                sprite.px(x, y, COLORS[mark])
    return sprite


def main():
    animals = {
        "deer": draw(DEER),
        "tiger": draw(TIGER),
        "wolf": draw(WOLF),
        "buffalo": draw(BUFFALO),
        "giraffe": draw(GIRAFFE),
    }
    sheet = Sprite(16 * len(animals), 16)
    for index, sprite in enumerate(animals.values()):
        for y in range(16):
            for x in range(16):
                color = sprite.get(x, y)
                if color is not None and color[3]:
                    sheet.px(index * 16 + x, y, color)
    sheet.preview(OUT / "preview.png", scale=8)
    for name, sprite in animals.items():
        sprite.save_png(OUT / f"{name}.png")
        sprite.save_silhouette(OUT / f"{name}_silhouette.png")
        sprite.stats()


if __name__ == "__main__":
    main()
