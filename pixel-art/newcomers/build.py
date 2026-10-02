"""Top-down 32x32 hare, jackal, and heron. Outlines stay lighter than pure black."""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "sprites"
OUTLINE = (72, 52, 88, 255)


def _canvas():
    return Image.new("RGBA", (32, 32), (0, 0, 0, 0))


def _hare():
    image = _canvas()
    draw = ImageDraw.Draw(image)
    draw.ellipse((12, 3, 16, 14), fill=(196, 154, 96, 255), outline=OUTLINE)
    draw.ellipse((17, 3, 21, 14), fill=(186, 140, 84, 255), outline=OUTLINE)
    draw.ellipse((8, 12, 24, 26), fill=(214, 176, 112, 255), outline=OUTLINE)
    draw.ellipse((13, 16, 16, 19), fill=(48, 36, 32, 255))
    draw.ellipse((18, 16, 21, 19), fill=(48, 36, 32, 255))
    draw.ellipse((10, 24, 14, 29), fill=(168, 124, 78, 255))
    draw.ellipse((18, 24, 22, 29), fill=(168, 124, 78, 255))
    return image


def _jackal():
    image = _canvas()
    draw = ImageDraw.Draw(image)
    draw.polygon([(10, 8), (8, 16), (13, 14)], fill=(214, 156, 72, 255), outline=OUTLINE)
    draw.polygon([(22, 8), (19, 14), (24, 16)], fill=(214, 156, 72, 255), outline=OUTLINE)
    draw.ellipse((7, 13, 25, 27), fill=(232, 176, 86, 255), outline=OUTLINE)
    draw.polygon([(14, 18), (18, 18), (16, 26)], fill=(186, 122, 58, 255), outline=OUTLINE)
    draw.ellipse((11, 16, 14, 19), fill=(40, 32, 28, 255))
    draw.ellipse((18, 16, 21, 19), fill=(40, 32, 28, 255))
    return image


def _heron():
    image = _canvas()
    draw = ImageDraw.Draw(image)
    draw.line((16, 8, 16, 22), fill=(92, 112, 128, 255), width=3)
    draw.ellipse((11, 10, 21, 20), fill=(168, 186, 198, 255), outline=OUTLINE)
    draw.polygon([(16, 8), (27, 10), (16, 12)], fill=(232, 168, 64, 255), outline=OUTLINE)
    draw.ellipse((12, 12, 15, 15), fill=(40, 32, 28, 255))
    draw.line((13, 20, 11, 29), fill=(92, 112, 128, 255), width=2)
    draw.line((19, 20, 21, 29), fill=(92, 112, 128, 255), width=2)
    return image


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    preview = Image.new("RGBA", (32 * 3 + 16, 48), (192, 212, 112, 255))
    for index, (name, image) in enumerate((("hare", _hare()), ("jackal", _jackal()), ("heron", _heron()))):
        image.save(OUT / f"{name}.png")
        preview.paste(image, (8 + index * 32, 8), image)
    preview.resize((preview.width * 6, preview.height * 6), Image.Resampling.NEAREST).save(
        Path(__file__).with_name("preview.png"))


if __name__ == "__main__":
    main()
