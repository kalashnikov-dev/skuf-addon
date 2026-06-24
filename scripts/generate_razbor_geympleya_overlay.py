"""Generate Razbor Geympleya (Gameplay Breakdown) multiblock overlays — monitor-shaped front face."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

MOD = "skufaddon"
MACHINE = "razbor_geympleya"
RES = Path(
    r"C:\Users\daynt\IdeaProjects\skuf-addon\src\main\resources\assets\skufaddon"
)
OUT = RES / "textures" / "block" / "multiblock" / MACHINE
ITEM_OUT = RES / "textures" / "item"

FRAME = 16

C_TRANS = (0, 0, 0, 0)
C_DARK = (20, 22, 28, 255)
C_BEZEL = (36, 38, 48, 255)
C_METAL = (72, 76, 86, 255)
C_LIGHT = (130, 134, 144, 255)
C_HILITE = (190, 194, 204, 255)
C_SCREEN_OFF = (18, 22, 32, 255)
C_SCREEN_ON = (28, 42, 68, 255)
C_PIXEL = (64, 180, 220, 255)
C_PIXEL_DIM = (40, 100, 140, 255)
C_LED_OFF = (44, 48, 40, 255)
C_LED_BLUE = (80, 160, 255, 255)
C_LED_RED = (255, 72, 64, 255)
C_STAND = (48, 50, 58, 255)
C_TEAR = (72, 130, 200, 220)

E_SCREEN = (100, 200, 255, 255)
E_PIXEL = (140, 220, 255, 255)
E_LED = (120, 200, 255, 255)
E_TEAR = (100, 180, 255, 255)


def blank() -> Image.Image:
    return Image.new("RGBA", (FRAME, FRAME), C_TRANS)


def put(img: Image.Image, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    if 0 <= x < FRAME and 0 <= y < FRAME:
        img.putpixel((x, y), color)


def rect(img: Image.Image, x0: int, y0: int, x1: int, y1: int, color) -> None:
    ImageDraw.Draw(img).rectangle((x0, y0, x1, y1), fill=color)


def draw_monitor_frame(img: Image.Image) -> None:
    rect(img, 2, 1, 13, 10, C_BEZEL)
    rect(img, 3, 2, 12, 9, C_DARK)
    rect(img, 3, 2, 12, 2, C_LIGHT)
    rect(img, 3, 9, 12, 9, C_METAL)
    rect(img, 11, 10, 12, 10, C_LED_OFF)


def draw_screen(img: Image.Image, lit: bool) -> None:
    rect(img, 4, 3, 11, 8, C_SCREEN_ON if lit else C_SCREEN_OFF)
    if lit:
        for x, y in ((5, 4), (7, 5), (9, 4), (6, 7), (10, 6), (8, 8)):
            put(img, x, y, C_PIXEL)
        for x, y in ((5, 6), (9, 7)):
            put(img, x, y, C_PIXEL_DIM)
    else:
        put(img, 7, 5, C_PIXEL_DIM)
        put(img, 8, 6, C_PIXEL_DIM)


def draw_stand(img: Image.Image) -> None:
    rect(img, 6, 11, 9, 13, C_STAND)
    put(img, 6, 11, C_LIGHT)
    put(img, 9, 13, C_DARK)


def draw_tear_drop(img: Image.Image) -> None:
    for x, y in ((2, 6), (2, 7), (3, 8)):
        put(img, x, y, C_TEAR)


def draw_led(img: Image.Image, color: tuple[int, int, int, int]) -> None:
    rect(img, 11, 10, 12, 10, color)
    put(img, 11, 10, C_HILITE if color != C_LED_OFF else C_DARK)


def draw_idle_front() -> Image.Image:
    img = blank()
    draw_monitor_frame(img)
    draw_screen(img, lit=False)
    draw_stand(img)
    draw_led(img, C_LED_OFF)
    return img


def draw_active_front() -> Image.Image:
    img = draw_idle_front()
    draw_screen(img, lit=True)
    draw_tear_drop(img)
    draw_led(img, C_LED_BLUE)
    return img


def draw_paused_front() -> Image.Image:
    img = draw_idle_front()
    draw_screen(img, lit=True)
    draw_led(img, C_LED_RED)
    return img


def draw_emissive(base: Image.Image, mode: str) -> Image.Image:
    img = blank()
    if mode == "idle":
        return img
    if mode == "paused":
        for x in range(4, 12):
            for y in range(3, 9):
                if base.getpixel((x, y))[3] > 0 and base.getpixel((x, y)) == C_SCREEN_ON:
                    put(img, x, y, E_SCREEN)
        put(img, 11, 10, (255, 100, 80, 255))
        return img
    for x in range(4, 12):
        for y in range(3, 9):
            if base.getpixel((x, y)) in (C_PIXEL, C_PIXEL_DIM):
                put(img, x, y, E_PIXEL)
    for x, y in ((2, 6), (2, 7), (3, 8)):
        put(img, x, y, E_TEAR)
    put(img, 11, 10, E_LED)
    return img


def draw_item_icon() -> Image.Image:
    img = Image.new("RGBA", (16, 16), C_TRANS)
    draw_monitor_frame(img)
    draw_screen(img, lit=True)
    draw_stand(img)
    draw_tear_drop(img)
    draw_led(img, C_LED_BLUE)
    return img


def write_overlays() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    idle = draw_idle_front()
    active = draw_active_front()
    paused = draw_paused_front()

    idle.save(OUT / "overlay_front.png")
    draw_emissive(idle, "idle").save(OUT / "overlay_front_emissive.png")
    paused.save(OUT / "overlay_front_paused.png")
    draw_emissive(paused, "paused").save(OUT / "overlay_front_paused_emissive.png")
    active.save(OUT / "overlay_front_active.png")
    draw_emissive(active, "active").save(OUT / "overlay_front_active_emissive.png")


def write_models() -> None:
    overlay_base = f"{MOD}:block/multiblock/{MACHINE}"
    block_model = {
        "parent": "minecraft:block/block",
        "loader": "gtceu:machine",
        "machine": f"{MOD}:{MACHINE}",
        "texture_overrides": {
            "all": "gtceu:block/casings/solid/machine_casing_inert_ptfe",
        },
        "variants": {},
    }
    for status, suffix in (
        ("idle", ""),
        ("suspend", "_paused"),
        ("waiting", "_active"),
        ("working", "_active"),
    ):
        block_model["variants"][f"recipe_logic_status={status}"] = {
            "model": {
                "parent": "gtceu:block/machine/template/cube_all/sided",
                "textures": {
                    "all": "gtceu:block/casings/solid/machine_casing_inert_ptfe",
                    "overlay_front": f"{overlay_base}/overlay_front{suffix}",
                    "overlay_front_emissive": f"{overlay_base}/overlay_front{suffix}_emissive",
                },
            }
        }

    blockstate: dict = {"variants": {}}
    for facing, rot in (("north", {}), ("south", {"y": 180}), ("west", {"y": 270}), ("east", {"y": 90})):
        entry: dict = {"model": f"{MOD}:block/machine/{MACHINE}"}
        entry.update(rot)
        blockstate["variants"][f"facing={facing}"] = entry

    (RES / "blockstates" / f"{MACHINE}.json").write_text(
        json.dumps(blockstate, indent=2) + "\n", encoding="utf-8"
    )
    (RES / "models" / "block" / "machine" / f"{MACHINE}.json").write_text(
        json.dumps(block_model, indent=2) + "\n", encoding="utf-8"
    )
    (RES / "models" / "item" / f"{MACHINE}.json").write_text(
        json.dumps({"parent": f"{MOD}:block/machine/{MACHINE}"}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_overlays()
    write_models()
    ITEM_OUT.mkdir(parents=True, exist_ok=True)
    draw_item_icon().save(ITEM_OUT / f"{MACHINE}.png")
    print(f"{MACHINE}: overlays, models, and item icon")


if __name__ == "__main__":
    main()
