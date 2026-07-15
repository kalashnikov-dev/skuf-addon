"""Generate only the burnt_capacitor item texture."""
from pathlib import Path

from PIL import Image

RES = Path(__file__).resolve().parents[1] / "src/main/resources/assets/skufaddon"


def make_burnt_capacitor_texture() -> None:
    """Burnt capacitor: warped charred can, ember glow, melted leads."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    char = (0x2A, 0x1E, 0x18, 255)
    char_hi = (0x4A, 0x32, 0x28, 255)
    char_lo = (0x12, 0x0C, 0x0A, 255)
    ember = (0xD0, 0x58, 0x18, 255)
    ember_hi = (0xF0, 0x90, 0x30, 255)
    ember_lo = (0x88, 0x28, 0x08, 255)
    ash = (0x1A, 0x1A, 0x1A, 255)
    melt_lead = (0x5A, 0x48, 0x30, 255)

    body_coords = [
        (6, 1), (7, 1), (8, 1), (9, 1),
        (5, 2), (6, 2), (7, 2), (8, 2), (9, 2), (10, 2),
        (5, 3), (6, 3), (7, 3), (8, 3), (9, 3), (10, 3), (11, 3),
        (5, 4), (6, 4), (7, 4), (8, 4), (9, 4), (10, 4), (11, 4),
        (5, 5), (6, 5), (7, 5), (8, 5), (9, 5), (10, 5), (11, 5),
        (5, 6), (6, 6), (7, 6), (8, 6), (9, 6), (10, 6), (11, 6),
        (6, 7), (7, 7), (8, 7), (9, 7), (10, 7), (11, 7),
        (6, 8), (7, 8), (8, 8), (9, 8), (10, 8), (11, 8),
        (7, 9), (8, 9), (9, 9), (10, 9), (11, 9),
        (8, 10), (9, 10), (10, 10),
    ]
    for x, y in body_coords:
        px[x, y] = char
    for x, y in [(5, y) for y in range(2, 7)] + [(6, 2), (6, 3)]:
        if 0 <= x < 16 and 0 <= y < 16:
            px[x, y] = char_hi
    for x, y in [(11, y) for y in range(3, 10)] + [(10, 9), (10, 10)]:
        px[x, y] = char_lo

    for x, y in [(7, 4), (8, 5), (9, 6), (8, 4), (7, 5)]:
        px[x, y] = ember
    px[8, 5] = ember_hi
    px[9, 5] = ember_lo
    px[10, 4] = ember_lo

    px[7, 1] = ash
    px[8, 1] = ember_lo
    px[6, 0] = (0x40, 0x38, 0x30, 180)
    px[7, 0] = (0x50, 0x48, 0x40, 140)
    px[8, 0] = (0x60, 0x50, 0x40, 100)

    px[6, 11] = melt_lead
    px[6, 12] = melt_lead
    px[5, 13] = melt_lead
    px[9, 11] = melt_lead
    px[10, 12] = (0x3A, 0x30, 0x22, 255)
    px[10, 13] = ember_lo

    out = RES / "textures" / "item" / "burnt_capacitor.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


if __name__ == "__main__":
    make_burnt_capacitor_texture()
    print("Generated burnt_capacitor.png only.")
