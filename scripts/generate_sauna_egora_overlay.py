"""Generate Sauna Egora multiblock controller overlays (GT-style front face + emissive)."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

MOD = "skufaddon"
RES = Path(
    r"C:\Users\daynt\IdeaProjects\skuf-addon\src\main\resources\assets\skufaddon"
)
OUT = RES / "textures" / "block" / "multiblock" / "sauna_egora"
ITEM_OUT = RES / "textures" / "item"

FRAME = 16

C_TRANS = (0, 0, 0, 0)
C_DARK = (34, 36, 40, 255)
C_METAL = (92, 96, 104, 255)
C_LIGHT = (148, 152, 160, 255)
C_HILITE = (198, 202, 210, 255)
C_GLASS = (72, 88, 100, 200)
C_GLASS_HOT = (110, 72, 48, 220)
C_STEAM = (210, 218, 228, 180)
C_STEAM_HOT = (255, 220, 180, 220)
C_THERMO_BG = (48, 52, 56, 255)
C_THERMO_COLD = (88, 160, 220, 255)
C_THERMO_WARM = (240, 160, 64, 255)
C_THERMO_HOT = (255, 96, 48, 255)
C_DROPLET = (196, 210, 130, 255)
C_LED_OFF = (52, 56, 48, 255)
C_LED_GREEN = (120, 255, 88, 255)
C_LED_ORANGE = (255, 170, 64, 255)

E_STEAM = (255, 200, 140, 255)
E_THERMO = (255, 120, 60, 255)
E_WINDOW = (255, 180, 100, 255)
E_DROPLET = (200, 255, 120, 255)


def blank() -> Image.Image:
    return Image.new("RGBA", (FRAME, FRAME), C_TRANS)


def put(img: Image.Image, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    if 0 <= x < FRAME and 0 <= y < FRAME:
        img.putpixel((x, y), color)


def rect(img: Image.Image, x0: int, y0: int, x1: int, y1: int, color) -> None:
    ImageDraw.Draw(img).rectangle((x0, y0, x1, y1), fill=color)


def draw_frame(img: Image.Image) -> None:
    rect(img, 1, 1, 14, 14, C_DARK)
    rect(img, 2, 2, 13, 13, C_METAL)
    rect(img, 3, 3, 12, 12, C_DARK)


def draw_sauna_window(img: Image.Image, hot: bool) -> None:
    rect(img, 5, 4, 10, 10, C_GLASS_HOT if hot else C_GLASS)
    put(img, 5, 4, C_HILITE)
    put(img, 10, 10, C_DARK)
    if hot:
        for x, y in ((6, 5), (8, 6), (7, 8), (9, 7)):
            put(img, x, y, C_STEAM_HOT)
    else:
        put(img, 7, 6, C_STEAM)
        put(img, 8, 8, C_STEAM)


def draw_thermometer(img: Image.Image, level: int) -> None:
    rect(img, 3, 5, 4, 11, C_THERMO_BG)
    put(img, 3, 5, C_LIGHT)
    colors = [C_THERMO_COLD, C_THERMO_WARM, C_THERMO_HOT, C_THERMO_HOT]
    for index, y in enumerate((10, 8, 6, 5)):
        color = colors[index] if index < level else C_DARK
        put(img, 4, y, color)
    put(img, 4, 11, C_THERMO_WARM if level >= 2 else C_THERMO_COLD)


def draw_droplet_output(img: Image.Image, lit: bool) -> None:
    color = C_DROPLET if lit else C_METAL
    for x, y in ((11, 10), (12, 11), (11, 12), (10, 11)):
        put(img, x, y, color)
    put(img, 11, 11, C_HILITE if lit else C_DARK)
    put(img, 12, 5, C_LED_ORANGE if lit else C_LED_OFF)


def draw_vent(img: Image.Image, hot: bool) -> None:
    for x in (11, 12):
        put(img, x, 6, C_HILITE if hot else C_METAL)
        put(img, x, 7, C_STEAM_HOT if hot else C_DARK)


def draw_idle_front() -> Image.Image:
    img = blank()
    draw_frame(img)
    draw_sauna_window(img, hot=False)
    draw_thermometer(img, level=1)
    draw_vent(img, hot=False)
    draw_droplet_output(img, lit=False)
    return img


def draw_active_front() -> Image.Image:
    img = draw_idle_front()
    draw_sauna_window(img, hot=True)
    draw_thermometer(img, level=4)
    draw_vent(img, hot=True)
    draw_droplet_output(img, lit=True)
    for x, y in ((6, 3), (9, 3), (12, 8)):
        put(img, x, y, C_STEAM_HOT)
    return img


def draw_paused_front() -> Image.Image:
    img = draw_idle_front()
    draw_sauna_window(img, hot=False)
    draw_thermometer(img, level=2)
    put(img, 12, 5, C_LED_ORANGE)
    return img


def draw_idle_emissive() -> Image.Image:
    img = blank()
    put(img, 7, 7, (80, 160, 220, 255))
    return img


def draw_active_emissive() -> Image.Image:
    img = blank()
    for x, y in ((6, 5), (8, 6), (7, 8), (9, 7), (6, 3), (9, 3)):
        put(img, x, y, E_STEAM)
    for y in (5, 6, 8, 10):
        put(img, 4, y, E_THERMO)
    put(img, 7, 7, E_WINDOW)
    for x, y in ((11, 10), (12, 11), (11, 12), (10, 11), (11, 11)):
        put(img, x, y, E_DROPLET)
    put(img, 12, 5, E_THERMO)
    return img


def draw_paused_emissive() -> Image.Image:
    img = blank()
    put(img, 4, 8, E_THERMO)
    put(img, 12, 5, (255, 200, 80, 255))
    return img


def draw_item_icon() -> Image.Image:
    """Inventory icon: plascrete-style casing with sauna overlay on the front face."""
    img = Image.new("RGBA", (16, 16), C_TRANS)
    base = (118, 122, 128, 255)
    dark = (82, 86, 92, 255)
    light = (158, 162, 170, 255)
    for y in range(16):
        for x in range(16):
            tone = base
            if x <= y:
                tone = dark
            if x + y < 8:
                tone = light
            img.putpixel((x, y), tone)
    overlay = draw_active_front()
    for y in range(3, 14):
        for x in range(3, 13):
            pixel = overlay.getpixel((x - 2, y - 2))
            if pixel[3] > 0:
                img.putpixel((x, y), pixel)
    return img


BLOCKSTATE = RES / "blockstates" / "sauna_egora.json"
BLOCK_MODEL = RES / "models" / "block" / "machine" / "sauna_egora.json"
ITEM_MODEL = RES / "models" / "item" / "sauna_egora.json"
OVERLAY_BASE = f"{MOD}:block/multiblock/sauna_egora"
CASING = "gtceu:block/casings/cleanroom/plascrete"


def write_block_model() -> None:
    variants = {}
    for status, suffix, emissive_suffix in (
        ("idle", "", "_emissive"),
        ("suspend", "_paused", "_paused_emissive"),
        ("waiting", "_active", "_active_emissive"),
        ("working", "_active", "_active_emissive"),
    ):
        variants[f"recipe_logic_status={status}"] = {
            "model": {
                "parent": "gtceu:block/machine/template/cube_all/sided",
                "textures": {
                    "all": CASING,
                    "overlay_front": f"{OVERLAY_BASE}/overlay_front{suffix}",
                    "overlay_front_emissive": f"{OVERLAY_BASE}/overlay_front{emissive_suffix}",
                },
            }
        }

    BLOCK_MODEL.parent.mkdir(parents=True, exist_ok=True)
    BLOCK_MODEL.write_text(
        json.dumps(
            {
                "parent": "minecraft:block/block",
                "loader": "gtceu:machine",
                "machine": f"{MOD}:sauna_egora",
                "texture_overrides": {"all": CASING},
                "variants": variants,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_blockstate() -> None:
    BLOCKSTATE.parent.mkdir(parents=True, exist_ok=True)
    BLOCKSTATE.write_text(
        json.dumps(
            {
                "variants": {
                    "facing=east": {
                        "model": f"{MOD}:block/machine/sauna_egora",
                        "y": 90,
                    },
                    "facing=north": {
                        "model": f"{MOD}:block/machine/sauna_egora",
                    },
                    "facing=south": {
                        "model": f"{MOD}:block/machine/sauna_egora",
                        "y": 180,
                    },
                    "facing=west": {
                        "model": f"{MOD}:block/machine/sauna_egora",
                        "y": 270,
                    },
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_item_model() -> None:
    ITEM_MODEL.parent.mkdir(parents=True, exist_ok=True)
    ITEM_MODEL.write_text(
        json.dumps({"parent": f"{MOD}:block/machine/sauna_egora"}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ITEM_OUT.mkdir(parents=True, exist_ok=True)

    pairs = (
        ("overlay_front.png", draw_idle_front()),
        ("overlay_front_active.png", draw_active_front()),
        ("overlay_front_paused.png", draw_paused_front()),
        ("overlay_front_emissive.png", draw_idle_emissive()),
        ("overlay_front_active_emissive.png", draw_active_emissive()),
        ("overlay_front_paused_emissive.png", draw_paused_emissive()),
    )
    for name, image in pairs:
        image.save(OUT / name)

    draw_item_icon().save(ITEM_OUT / "sauna_egora.png")
    write_block_model()
    write_blockstate()
    write_item_model()
    print("sauna egora overlays, block model, and item icon")


if __name__ == "__main__":
    main()
