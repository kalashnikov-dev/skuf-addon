"""Generate Skufizator multiblock controller overlays (GT-style front face + emissive)."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

MOD = "skufaddon"
RES = Path(
    r"C:\Users\daynt\IdeaProjects\skuf-addon\src\main\resources\assets\skufaddon"
)
OUT = RES / "textures" / "block" / "multiblock" / "skufizator"
ITEM_OUT = RES / "textures" / "item"

FRAME = 16

C_TRANS = (0, 0, 0, 0)
C_DARK = (28, 30, 36, 255)
C_METAL = (88, 92, 100, 255)
C_LIGHT = (150, 154, 162, 255)
C_HILITE = (206, 210, 218, 255)
C_SCREEN = (42, 48, 56, 255)
C_SCREEN_ON = (58, 72, 88, 255)
C_CORE_IDLE = (52, 118, 44, 255)
C_CORE_ACTIVE = (96, 220, 72, 255)
C_CORE_HOT = (140, 255, 108, 255)
C_LED_OFF = (48, 52, 44, 255)
C_LED_GREEN = (120, 255, 88, 255)
C_LED_YELLOW = (255, 210, 64, 255)
C_LED_RED = (255, 88, 72, 255)
C_CHUTE = (64, 68, 74, 255)

E_CORE_IDLE = (40, 180, 32, 255)
E_CORE_ACTIVE = (120, 255, 80, 255)
E_SCREEN = (80, 200, 255, 255)
E_LED_GREEN = (140, 255, 100, 255)
E_LED_YELLOW = (255, 230, 80, 255)


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


def draw_display(img: Image.Image, lit: bool) -> None:
    rect(img, 4, 3, 11, 4, C_SCREEN_ON if lit else C_SCREEN)
    for x in range(5, 11):
        put(img, x, 4, C_HILITE if lit and x % 2 == 0 else C_LIGHT if lit else C_METAL)


def draw_input_chute(img: Image.Image) -> None:
    rect(img, 3, 5, 4, 10, C_CHUTE)
    put(img, 3, 5, C_LIGHT)
    put(img, 4, 10, C_DARK)


def draw_reactor(img: Image.Image, core: tuple[int, int, int, int], ring: tuple[int, int, int, int]) -> None:
    for x, y in ((6, 6), (7, 6), (8, 6), (6, 7), (8, 7), (6, 8), (7, 8), (8, 8)):
        put(img, x, y, ring)
    put(img, 7, 7, core)
    put(img, 6, 7, C_DARK)
    put(img, 8, 7, C_DARK)
    put(img, 7, 6, C_LIGHT)
    put(img, 7, 8, C_DARK)


def draw_led_column(img: Image.Image, colors: list[tuple[int, int, int, int]]) -> None:
    for index, led_y in enumerate((5, 7, 9, 11)):
        color = colors[index] if index < len(colors) else C_LED_OFF
        rect(img, 11, led_y, 12, led_y, color)
        put(img, 11, led_y, C_HILITE if color != C_LED_OFF else C_DARK)


def draw_output_slot(img: Image.Image, lit: bool) -> None:
    rect(img, 5, 12, 10, 13, C_CHUTE)
    put(img, 5, 12, C_LIGHT if lit else C_METAL)
    put(img, 10, 13, C_DARK)


def draw_idle_front() -> Image.Image:
    img = blank()
    draw_frame(img)
    draw_display(img, lit=False)
    draw_input_chute(img)
    draw_reactor(img, C_CORE_IDLE, C_METAL)
    draw_led_column(img, [C_LED_OFF, C_LED_OFF, C_LED_OFF, C_LED_OFF])
    draw_output_slot(img, lit=False)
    return img


def draw_active_front() -> Image.Image:
    img = draw_idle_front()
    draw_display(img, lit=True)
    draw_reactor(img, C_CORE_ACTIVE, C_LIGHT)
    draw_led_column(
        img,
        [C_LED_GREEN, C_LED_GREEN, C_LED_YELLOW, C_LED_GREEN],
    )
    draw_output_slot(img, lit=True)
    # Arcing energy lines around the pukan core.
    for x, y in ((5, 7), (9, 7), (7, 5), (7, 9)):
        put(img, x, y, C_HILITE)
    return img


def draw_paused_front() -> Image.Image:
    img = draw_idle_front()
    draw_display(img, lit=True)
    draw_reactor(img, C_CORE_IDLE, C_METAL)
    draw_led_column(img, [C_LED_YELLOW, C_LED_OFF, C_LED_OFF, C_LED_OFF])
    return img


def draw_idle_emissive() -> Image.Image:
    img = blank()
    put(img, 7, 7, E_CORE_IDLE)
    return img


def draw_active_emissive() -> Image.Image:
    img = blank()
    for x in range(5, 11):
        put(img, x, 4, E_SCREEN)
    for x, y in ((6, 6), (8, 6), (6, 8), (8, 8), (7, 7)):
        put(img, x, y, E_CORE_ACTIVE)
    for led_y in (5, 7, 9, 11):
        put(img, 11, led_y, E_LED_GREEN)
    put(img, 12, 9, E_LED_YELLOW)
    return img


def draw_paused_emissive() -> Image.Image:
    img = blank()
    put(img, 7, 7, E_CORE_IDLE)
    put(img, 11, 5, E_LED_YELLOW)
    put(img, 5, 4, E_SCREEN)
    return img


def draw_item_icon() -> Image.Image:
    """Inventory icon: dull frame block with controller overlay on the front face."""
    img = Image.new("RGBA", (16, 16), C_TRANS)
    base = (108, 112, 118, 255)
    dark = (72, 76, 82, 255)
    light = (148, 152, 160, 255)
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


BLOCKSTATE = RES / "blockstates" / "skufizator.json"
BLOCK_MODEL = RES / "models" / "block" / "machine" / "skufizator.json"
ITEM_MODEL = RES / "models" / "item" / "skufizator.json"
OVERLAY_BASE = f"{MOD}:block/multiblock/skufizator"
CASING = "gtceu:block/material_sets/dull/frame_gt"


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
                "machine": f"{MOD}:skufizator",
                "texture_overrides": {"all": CASING},
                "variants": variants,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_blockstate() -> None:
    facings = []
    for facing, y in (
        ("north", None),
        ("south", 180),
        ("east", 90),
        ("west", 270),
    ):
        for upwards, z in (
            ("north", None),
            ("south", 180),
            ("east", 270),
            ("west", 90),
        ):
            key = f"facing={facing},upwards_facing={upwards}"
            entry: dict = {"model": f"{MOD}:block/machine/skufizator"}
            if y is not None:
                entry["y"] = y
            if z is not None:
                entry["gtceu:z"] = z
            facings.append((key, entry))

    for upwards, z in (("east", 90), ("north", 180), ("south", None), ("west", 270)):
        key = f"facing=up,upwards_facing={upwards}"
        entry = {"model": f"{MOD}:block/machine/skufizator", "x": 270}
        if z is not None:
            entry["gtceu:z"] = z
        facings.append((key, entry))

    for upwards, z in (("east", 90), ("north", None), ("south", 180), ("west", 270)):
        key = f"facing=down,upwards_facing={upwards}"
        entry = {"model": f"{MOD}:block/machine/skufizator", "x": 90}
        if z is not None:
            entry["gtceu:z"] = z
        facings.append((key, entry))

    BLOCKSTATE.parent.mkdir(parents=True, exist_ok=True)
    BLOCKSTATE.write_text(
        json.dumps({"variants": dict(facings)}, indent=2) + "\n",
        encoding="utf-8",
    )


def write_item_model() -> None:
    ITEM_MODEL.parent.mkdir(parents=True, exist_ok=True)
    ITEM_MODEL.write_text(
        json.dumps({"parent": f"{MOD}:block/machine/skufizator"}, indent=2) + "\n",
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

    draw_item_icon().save(ITEM_OUT / "skufizator.png")
    write_block_model()
    write_blockstate()
    write_item_model()
    print("skufizator overlays, models, and item icon")


if __name__ == "__main__":
    main()
