"""Generate the Pukan Core Casing block texture (matches item/pukan_core palette)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(r"C:\Users\daynt\IdeaProjects\skuf-addon\src\main\resources\assets\skufaddon")
OUT = ROOT / "textures" / "block" / "pukan_core_casing.png"
CORE_ITEM = ROOT / "textures" / "item" / "pukan_core.png"

FRAME = 16

C_VOID = (12, 13, 18, 255)
C_DARK = (18, 19, 24, 255)
C_METAL = (56, 58, 64, 255)
C_PLATE = (83, 86, 95, 255)
C_LIGHT = (95, 100, 110, 255)
C_HILITE = (96, 101, 111, 255)
C_BOLT = (77, 80, 87, 255)
C_FRAME = (16, 19, 26, 255)
C_RED = (149, 28, 28, 255)
C_RED_DARK = (142, 27, 16, 255)
C_AMBER = (248, 140, 33, 255)
C_YELLOW = (255, 203, 76, 255)


def put(img: Image.Image, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    if 0 <= x < FRAME and 0 <= y < FRAME:
        img.putpixel((x, y), color)


def rect(img: Image.Image, x0: int, y0: int, x1: int, y1: int, color) -> None:
    ImageDraw.Draw(img).rectangle((x0, y0, x1, y1), fill=color)


def load_core_preview() -> Image.Image:
    sheet = Image.open(CORE_ITEM).convert("RGBA")
    return sheet.crop((0, 0, 16, 16))


def draw_casing() -> Image.Image:
    img = Image.new("RGBA", (FRAME, FRAME), C_VOID)
    rect(img, 0, 0, 15, 15, C_DARK)
    rect(img, 1, 1, 14, 14, C_METAL)
    rect(img, 2, 2, 13, 13, C_PLATE)

    # Shell plating.
    for i in range(2, 14):
        put(img, i, 2, C_LIGHT if i % 3 == 0 else C_METAL)
        put(img, i, 13, C_DARK if i % 3 == 0 else C_METAL)
        put(img, 2, i, C_LIGHT if i % 3 == 0 else C_METAL)
        put(img, 13, i, C_DARK if i % 3 == 0 else C_METAL)

    # Red energy channels instead of green conduits.
    for x in range(3, 13):
        y = x if x < 8 else 15 - x
        put(img, x, y, C_RED_DARK if (x + y) % 2 == 0 else C_RED)
        put(img, x, 14 - y, C_RED_DARK if (x + y) % 2 == 0 else C_RED)

    # Corner bolts.
    for x, y in ((3, 3), (12, 3), (3, 12), (12, 12)):
        put(img, x, y, C_BOLT)
        put(img, x + 1, y, C_HILITE)
        put(img, x, y + 1, C_DARK)

    # Viewport frame.
    rect(img, 5, 5, 10, 10, C_FRAME)
    rect(img, 6, 6, 9, 9, C_DARK)

    # Embed the actual pukan core icon in the sight glass.
    core = load_core_preview()
    for y in range(6, 10):
        for x in range(6, 10):
            pixel = core.getpixel((x, y))
            if pixel[3] > 0:
                img.putpixel((x, y), pixel)

    # Warm rim glow around the embedded core.
    for x, y in ((5, 7), (5, 8), (10, 7), (10, 8), (7, 5), (8, 5), (7, 10), (8, 10)):
        existing = img.getpixel((x, y))
        if existing[3] == 0 or existing[:3] == C_FRAME[:3]:
            put(img, x, y, C_AMBER if (x + y) % 2 == 0 else C_RED)

    # Status indicators: red / amber like the core item.
    put(img, 4, 11, C_RED)
    put(img, 11, 11, C_AMBER)
    put(img, 7, 12, C_YELLOW)
    put(img, 8, 12, C_RED_DARK)

    # Bevel highlights.
    put(img, 1, 1, C_HILITE)
    put(img, 2, 1, C_LIGHT)
    put(img, 1, 2, C_LIGHT)
    put(img, 14, 14, C_DARK)
    put(img, 13, 14, C_DARK)
    put(img, 14, 13, C_DARK)

    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    draw_casing().save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
