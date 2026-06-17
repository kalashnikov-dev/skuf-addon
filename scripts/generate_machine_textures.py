"""Generate GT-style machine overlay textures for all Skuf singleblock machines."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw

TEXTURES_ROOT = Path(
    r"C:\Users\daynt\IdeaProjects\skuf-addon\src\main\resources\assets\skufaddon\textures\block\machines"
)
REF = Path(r"C:\Users\daynt\IdeaProjects\skuf-addon\build\gt_ref\centrifuge")
REF_DISTILLERY = Path(r"C:\Users\daynt\IdeaProjects\skuf-addon\build\gt_ref\distillery")

FRAME = 16
ACTIVE_FRAMES = 8
ACTIVE_META = (
    "{\n"
    '  "animation": {\n'
    '    "frametime": 4,\n'
    '    "width": 16,\n'
    '    "height": 16,\n'
    '    "interpolate": true\n'
    "  }\n"
    "}\n"
)

C_TRANS = (0, 0, 0, 0)
C_DARK = (34, 34, 42, 255)
C_METAL = (92, 96, 104, 255)
C_LIGHT = (156, 160, 168, 255)
C_HILITE = (210, 214, 222, 255)
C_ACTIVE = (238, 240, 245, 255)
C_ACTIVE_MID = (186, 190, 198, 255)
C_ACTIVE_DIM = (132, 136, 144, 255)
C_FLUID = (108, 114, 124, 255)
C_FLUID_BRIGHT = (168, 174, 184, 255)
C_GLASS = (72, 76, 84, 255)
C_WARM = (255, 148, 48, 255)
C_WARM_MID = (220, 108, 32, 255)
C_WARM_DIM = (168, 72, 24, 255)
C_LED_ON = (188, 255, 118, 255)
C_LED_DIM = (72, 120, 48, 255)

DrawFn = Callable[[Image.Image], None]
ActiveFn = Callable[[Image.Image, int], None]


def blank() -> Image.Image:
    return Image.new("RGBA", (FRAME, FRAME), C_TRANS)


def put(img: Image.Image, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    if 0 <= x < FRAME and 0 <= y < FRAME:
        img.putpixel((x, y), color)


def clamp(value: int, low: int = 0, high: int = 255) -> int:
    return max(low, min(high, value))


def tint(color: tuple[int, int, int, int], amount: int) -> tuple[int, int, int, int]:
    r, g, b, a = color
    return (clamp(r + amount), clamp(g + amount), clamp(b + amount), a)


def rect(img: Image.Image, x0: int, y0: int, x1: int, y1: int, color) -> None:
    ImageDraw.Draw(img).rectangle((x0, y0, x1, y1), fill=color)


def frame_sheet(frames: list[Image.Image]) -> Image.Image:
    sheet = Image.new("RGBA", (FRAME, FRAME * len(frames)), C_TRANS)
    for index, frame in enumerate(frames):
        sheet.paste(frame, (0, index * FRAME))
    return sheet


def draw_pipe_column(img: Image.Image, x: int, y0: int, y1: int) -> None:
    rect(img, x, y0, x, y1, C_DARK)
    rect(img, x + 1, y0, x + 1, y1, C_METAL)
    put(img, x, y0, C_HILITE)
    put(img, x + 1, y0, C_LIGHT)


def back_idle() -> Image.Image:
    ref = REF / "overlay_back.png"
    if ref.exists():
        return Image.open(ref).convert("RGBA")
    return blank()


def make_idle(draw: DrawFn) -> Image.Image:
    img = blank()
    draw(img)
    return img


def make_active(draw: DrawFn, animate: ActiveFn) -> Image.Image:
    frames: list[Image.Image] = []
    for phase in range(ACTIVE_FRAMES):
        img = make_idle(draw)
        animate(img, phase)
        frames.append(img)
    return frame_sheet(frames)


def save_machine(
    machine_id: str,
    front: DrawFn,
    front_active: ActiveFn,
    side: DrawFn,
    side_active: ActiveFn,
    top: DrawFn,
    top_active: ActiveFn,
) -> None:
    out = TEXTURES_ROOT / machine_id
    out.mkdir(parents=True, exist_ok=True)

    def write(name: str, image: Image.Image, meta: str | None = None) -> None:
        image.save(out / name)
        meta_path = out / f"{name}.mcmeta"
        if meta is not None:
            meta_path.write_text(meta, encoding="utf-8")
        elif meta_path.exists():
            meta_path.unlink()

    write("overlay_front.png", make_idle(front))
    write("overlay_front_active.png", make_active(front, front_active), ACTIVE_META)
    write("overlay_side.png", make_idle(side))
    write("overlay_side_active.png", make_active(side, side_active), ACTIVE_META)
    write("overlay_top.png", make_idle(top))
    write("overlay_top_active.png", make_active(top, top_active), ACTIVE_META)
    write("overlay_back.png", back_idle())
    write("overlay_back_active.png", back_idle())
    print(machine_id)


# --- Normis Filtration Machine ---


def normis_front(img: Image.Image) -> None:
    draw_pipe_column(img, 1, 3, 12)
    draw_pipe_column(img, 13, 3, 12)
    rect(img, 4, 4, 11, 11, C_DARK)
    rect(img, 5, 5, 10, 10, C_METAL)
    for x in range(5, 11, 2):
        for y in range(5, 11, 2):
            put(img, x, y, C_LIGHT)
            if x + 1 <= 10:
                put(img, x + 1, y, C_DARK)
    rect(img, 6, 2, 9, 3, C_METAL)


def normis_front_active(img: Image.Image, phase: int) -> None:
    highlight_row = 5 + (phase % 3) * 2
    for x in range(5, 11, 2):
        for y in range(5, 11, 2):
            if y == highlight_row:
                put(img, x, y, C_ACTIVE)
                if x + 1 <= 10:
                    put(img, x + 1, y, C_ACTIVE_MID)
    flow_y = 5 + phase % 6
    put(img, 7, flow_y, C_ACTIVE)
    put(img, 7, 10, C_ACTIVE if phase % 2 == 0 else C_ACTIVE_MID)


def normis_side(img: Image.Image) -> None:
    rect(img, 2, 2, 13, 13, C_DARK)
    rect(img, 3, 3, 12, 12, C_METAL)
    rect(img, 5, 4, 10, 11, C_DARK)
    rect(img, 6, 5, 9, 10, C_GLASS)
    draw_pipe_column(img, 14, 4, 11)


def normis_side_active(img: Image.Image, phase: int) -> None:
    fill_height = phase + 1
    top = max(10 - fill_height + 1, 5)
    for y in range(10, top - 1, -1):
        shade = C_FLUID if y % 2 == 0 else C_FLUID_BRIGHT
        put(img, 7, y, C_ACTIVE if y == top else shade)


def normis_top(img: Image.Image) -> None:
    rect(img, 3, 3, 12, 12, C_DARK)
    rect(img, 4, 4, 11, 11, C_METAL)
    rect(img, 6, 6, 9, 9, C_DARK)
    rect(img, 7, 7, 8, 8, C_GLASS)


def normis_top_active(img: Image.Image, phase: int) -> None:
    cx, cy = 7, 7
    ring_radius = 1 + phase % 4
    for x in range(4, 12):
        for y in range(4, 12):
            if abs(x - cx) + abs(y - cy) == ring_radius:
                put(img, x, y, C_ACTIVE if (x + phase) % 2 == 0 else C_ACTIVE_MID)
    put(img, cx, cy, C_ACTIVE if phase % 2 == 0 else C_ACTIVE_MID)


# --- CNC Machine ---


def cnc_front(img: Image.Image) -> None:
    rect(img, 3, 9, 12, 10, C_METAL)
    rect(img, 3, 4, 12, 4, C_DARK)
    rect(img, 7, 4, 8, 9, C_DARK)
    put(img, 7, 9, C_HILITE)
    put(img, 8, 9, C_LIGHT)
    rect(img, 4, 11, 11, 12, C_DARK)
    for x in range(4, 12, 2):
        put(img, x, 11, C_METAL)


def cnc_front_active(img: Image.Image, phase: int) -> None:
    tool_x = 6 + phase % 4
    rect(img, tool_x, 4, tool_x + 1, 9, C_DARK)
    put(img, tool_x, 4, C_ACTIVE)
    put(img, tool_x + 1, 4, C_HILITE)
    put(img, tool_x, 9, C_ACTIVE_MID)
    put(img, tool_x, 10, C_ACTIVE if phase % 2 == 0 else C_ACTIVE_DIM)


def cnc_side(img: Image.Image) -> None:
    rect(img, 2, 10, 13, 11, C_METAL)
    rect(img, 2, 6, 13, 7, C_DARK)
    rect(img, 9, 5, 10, 10, C_METAL)
    rect(img, 3, 3, 5, 5, C_DARK)


def cnc_side_active(img: Image.Image, phase: int) -> None:
    carriage_x = 4 + phase % 5
    rect(img, carriage_x, 5, carriage_x + 2, 9, C_METAL)
    put(img, carriage_x + 1, 5, C_ACTIVE)
    put(img, carriage_x + 1, 9, C_ACTIVE_MID)


def cnc_top(img: Image.Image) -> None:
    rect(img, 4, 4, 11, 11, C_DARK)
    rect(img, 5, 5, 10, 10, C_METAL)
    for x, y in ((6, 7), (7, 6), (8, 7), (7, 8)):
        put(img, x, y, C_LIGHT)


def cnc_top_active(img: Image.Image, phase: int) -> None:
    cx, cy = 7, 7
    offsets = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    ox, oy = offsets[phase % 4]
    put(img, cx + ox, cy + oy, C_ACTIVE)
    put(img, cx, cy, C_HILITE if phase % 2 == 0 else C_ACTIVE_MID)


# --- Pot Distillery (GT distillery silhouette, neutral fluid colors) ---


def recolor_distillery_pixel(r: int, g: int, b: int, a: int) -> tuple[int, int, int, int]:
    if a == 0:
        return C_TRANS
    if r > 80 and g < 60 and b < 60:
        if r > 200:
            return C_FLUID_BRIGHT
        if r > 140:
            return C_FLUID
        if r > 90:
            return C_GLASS
        return C_DARK
    if r > 100 and g > 70 and b < 80:
        if r > 170:
            return C_LIGHT
        if r > 120:
            return C_METAL
        return C_DARK
    if g > 90 and r < 80:
        return C_METAL
    brightness = (r + g + b) // 3
    if brightness > 175:
        return C_HILITE
    if brightness > 135:
        return C_LIGHT
    if brightness > 85:
        return C_METAL
    if brightness > 40:
        return C_DARK
    return (25, 25, 25, 255)


def load_distillery_base(name: str) -> Image.Image:
    source = REF_DISTILLERY / f"{name}.png"
    if not source.exists():
        return blank()
    img = Image.open(source).convert("RGBA")
    out = blank()
    for y in range(FRAME):
        for x in range(FRAME):
            r, g, b, a = img.getpixel((x, y))
            out.putpixel((x, y), recolor_distillery_pixel(r, g, b, a))
    return out


def pot_front(img: Image.Image) -> None:
    img.paste(load_distillery_base("overlay_front"), (0, 0))


def pot_front_active(img: Image.Image, phase: int) -> None:
    # Sight glass boil (x 4-6, y 4-6).
    level = 6 - (phase % 3)
    for y in range(6, level - 1, -1):
        for x in range(4, 7):
            put(img, x, y, C_FLUID_BRIGHT if (x + y + phase) % 2 == 0 else C_FLUID)
    bubble_x = 4 + (phase % 3)
    put(img, bubble_x, level - 1, C_ACTIVE)
    put(img, 5, level - 2 if level > 5 else 5, C_ACTIVE_MID)
    # Heating coil glow under the still.
    for x in range(2, 9):
        warm = C_WARM if (x + phase) % 3 == 0 else C_WARM_MID if (x + phase) % 3 == 1 else C_WARM_DIM
        put(img, x, 7 + (phase % 2), warm)
        put(img, x, 8, C_WARM_DIM if phase % 2 else C_WARM_MID)
        put(img, x, 9, C_WARM if (x + phase) % 2 == 0 else C_WARM_DIM)
    # Status LEDs on the condenser column.
    for led_y, bit in ((4, 0), (6, 1), (8, 2)):
        color = C_LED_ON if (phase + bit) % 3 != 0 else C_LED_DIM
        put(img, 11, led_y, color)
        put(img, 12, led_y, C_LED_DIM if color == C_LED_ON else C_DARK)
    # Outlet drip on the right condenser pipe.
    drip_y = 11 + (phase % 3)
    if drip_y <= 13:
        put(img, 11, drip_y, C_ACTIVE)
        put(img, 12, drip_y, C_ACTIVE_MID)


def pot_side(img: Image.Image) -> None:
    img.paste(load_distillery_base("overlay_side"), (0, 0))


def pot_side_active(img: Image.Image, phase: int) -> None:
    # Twin distillation columns (left x 4-5, right x 11-12).
    left_level = 12 - (phase % 4)
    right_level = 12 - ((phase + 2) % 4)
    for y in range(12, left_level - 1, -1):
        put(img, 4, y, C_FLUID if y % 2 == 0 else C_FLUID_BRIGHT)
        put(img, 5, y, C_FLUID_BRIGHT if y % 2 == 0 else C_FLUID)
    for y in range(12, right_level - 1, -1):
        put(img, 11, y, C_FLUID_BRIGHT if y % 2 == 0 else C_FLUID)
        put(img, 12, y, C_FLUID if y % 2 == 0 else C_FLUID_BRIGHT)
    put(img, 4, left_level, C_ACTIVE)
    put(img, 11, right_level, C_ACTIVE)
    # Bottom reboiler glow.
    for x in range(4, 6):
        put(img, x, 12, C_WARM if (x + phase) % 2 == 0 else C_WARM_MID)
    for x in range(11, 13):
        put(img, x, 12, C_WARM_MID if (x + phase) % 2 == 0 else C_WARM_DIM)
    # Column status lamps.
    put(img, 3, 3 + (phase % 4) * 2, C_LED_ON)
    put(img, 13, 3 + ((phase + 2) % 4) * 2, C_LED_ON)


def pot_top(img: Image.Image) -> None:
    img.paste(load_distillery_base("overlay_top"), (0, 0))


def pot_top_active(img: Image.Image, phase: int) -> None:
    # Steam rising from the condenser opening above the heating grid.
    vent_y = 2 + (phase % 3)
    put(img, 7, vent_y, C_ACTIVE_DIM)
    put(img, 8, vent_y, C_ACTIVE)
    if vent_y > 2:
        put(img, 7, vent_y - 1, C_ACTIVE)
    # Heating grid cells pulse warm.
    for y in range(5, 11):
        for x in range(4, 12):
            if (x + y) % 2 == 0 and (x + y + phase) % 4 < 2:
                put(img, x, y, C_WARM_DIM if (x + y) % 4 else C_WARM_MID)
    put(img, 7, 8, C_WARM if phase % 2 == 0 else C_WARM_MID)
    put(img, 8, 7, C_WARM_MID)
    put(img, 7, 4, C_LED_ON if phase % 2 == 0 else C_LED_DIM)
    put(img, 8, 4, C_LED_DIM if phase % 2 == 0 else C_LED_ON)


# --- Vibe Stabilizer ---


def vibe_front(img: Image.Image) -> None:
    rect(img, 3, 3, 12, 12, C_DARK)
    rect(img, 4, 4, 11, 11, C_METAL)
    for x in range(4, 12):
        y = 8 + (1 if x % 4 in (0, 3) else -1 if x % 4 == 1 else 0)
        put(img, x, y, C_LIGHT)
    rect(img, 7, 10, 8, 11, C_DARK)


def vibe_front_active(img: Image.Image, phase: int) -> None:
    amplitude = max(0, 2 - phase // 3)
    for x in range(4, 12):
        wave = amplitude if x % 2 == phase % 2 else 0
        put(img, x, 8 - wave, C_ACTIVE)
        put(img, x, 8 + wave, C_ACTIVE_MID)
    put(img, 7, 10, C_ACTIVE if phase % 2 == 0 else C_HILITE)


def vibe_side(img: Image.Image) -> None:
    rect(img, 4, 3, 11, 12, C_DARK)
    rect(img, 5, 4, 10, 11, C_METAL)
    for y in range(5, 11):
        put(img, 6, y, C_LIGHT if y % 2 == 0 else C_DARK)
        put(img, 9, y, C_DARK if y % 2 == 0 else C_LIGHT)


def vibe_side_active(img: Image.Image, phase: int) -> None:
    bar = 6 + phase % 3
    for y in range(5, 11):
        shade = C_ACTIVE if y == bar else C_ACTIVE_DIM if abs(y - bar) == 1 else C_METAL
        put(img, 7, y, shade)
        put(img, 8, y, shade)


def vibe_top(img: Image.Image) -> None:
    rect(img, 4, 4, 11, 11, C_DARK)
    put(img, 7, 4, C_METAL)
    put(img, 7, 11, C_METAL)
    put(img, 4, 7, C_METAL)
    put(img, 11, 7, C_METAL)
    put(img, 7, 7, C_HILITE)


def vibe_top_active(img: Image.Image, phase: int) -> None:
    pulse = phase % 4
    for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        if (dx + dy + pulse) % 2 == 0:
            put(img, 7 + dx, 7 + dy, C_ACTIVE)
    put(img, 7, 7, C_HILITE)


MACHINES = {
    "normis_filtration_machine": (normis_front, normis_front_active, normis_side, normis_side_active, normis_top, normis_top_active),
    "cnc_machine": (cnc_front, cnc_front_active, cnc_side, cnc_side_active, cnc_top, cnc_top_active),
    "pot_distillery": (pot_front, pot_front_active, pot_side, pot_side_active, pot_top, pot_top_active),
    "vibe_stabilizer": (vibe_front, vibe_front_active, vibe_side, vibe_side_active, vibe_top, vibe_top_active),
}


def main() -> None:
    for machine_id, handlers in MACHINES.items():
        save_machine(machine_id, *handlers)


if __name__ == "__main__":
    main()
