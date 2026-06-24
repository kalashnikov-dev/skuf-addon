"""Generate Raw Demo (VHS-style) item texture."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

MOD = "skufaddon"
RES = Path(r"C:\Users\daynt\IdeaProjects\skuf-addon\src\main\resources\assets\skufaddon")
ITEM_OUT = RES / "textures" / "item"


def draw_raw_demo() -> Image.Image:
    """Small VHS cassette — dark shell, label strip, tape window."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    shell = (34, 36, 42, 255)
    shell_hi = (58, 60, 68, 255)
    shell_lo = (22, 24, 28, 255)
    label = (232, 228, 210, 255)
    label_txt = (196, 48, 48, 255)
    window = (14, 16, 22, 255)
    reel = (58, 42, 30, 255)
    reel_hi = (96, 72, 48, 255)
    tape = (40, 32, 28, 255)

    d.rectangle((3, 2, 12, 13), fill=shell)
    d.rectangle((3, 2, 12, 2), fill=shell_hi)
    d.rectangle((3, 13, 12, 13), fill=shell_lo)
    d.rectangle((3, 2, 3, 13), fill=shell_hi)
    d.rectangle((4, 3, 11, 5), fill=label)
    d.rectangle((5, 4, 7, 4), fill=label_txt)
    d.rectangle((9, 4, 10, 4), fill=label_txt)
    d.rectangle((5, 6, 10, 11), fill=window)
    d.rectangle((6, 7, 7, 9), fill=reel)
    d.rectangle((9, 8, 10, 10), fill=reel)
    img.putpixel((6, 7), reel_hi)
    img.putpixel((9, 8), reel_hi)
    d.rectangle((7, 9, 9, 9), fill=tape)
    for x, y in ((4, 12), (11, 12)):
        img.putpixel((x, y), shell_hi)

    return img


def write_item_model(name: str) -> None:
    path = RES / "models" / "item" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "parent": "minecraft:item/generated",
                "textures": {"layer0": f"{MOD}:item/{name}"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    ITEM_OUT.mkdir(parents=True, exist_ok=True)
    draw_raw_demo().save(ITEM_OUT / "raw_demo.png")
    write_item_model("raw_demo")
    print("Wrote raw_demo item texture + model")


if __name__ == "__main__":
    main()
