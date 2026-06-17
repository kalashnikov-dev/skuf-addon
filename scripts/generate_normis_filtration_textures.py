from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(
    r"C:\Users\daynt\IdeaProjects\skuf-addon\src\main\resources\assets\skufaddon\textures\block\machines\normis_filtration_machine"
)
REF = Path(r"C:\Users\daynt\IdeaProjects\skuf-addon\build\gt_ref\centrifuge")

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
# Neutral industrial palette — not tied to any specific fluid/material.
C_ACTIVE = (238, 240, 245, 255)
C_ACTIVE_MID = (186, 190, 198, 255)
C_ACTIVE_DIM = (132, 136, 144, 255)
C_FLUID = (108, 114, 124, 255)
C_FLUID_BRIGHT = (168, 174, 184, 255)
C_GLASS = (72, 76, 84, 255)


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


def overlay_front_idle() -> Image.Image:
    img = blank()
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
    put(img, 7, 2, C_HILITE)
    put(img, 8, 2, C_HILITE)
    return img


def overlay_front_active(phase: int) -> Image.Image:
    img = overlay_front_idle()

    # Scanning highlight across filter rows — generic "processing" pulse.
    highlight_row = 5 + (phase % 3) * 2
    for x in range(5, 11, 2):
        for y in range(5, 11, 2):
            if y == highlight_row:
                put(img, x, y, C_ACTIVE)
                if x + 1 <= 10:
                    put(img, x + 1, y, C_ACTIVE_MID)
            else:
                put(img, x, y, tint(C_LIGHT, -10))
                if x + 1 <= 10:
                    put(img, x + 1, y, C_DARK)

    # Flow indicator moving through the filter — neutral bright streak.
    flow_y = 5 + (phase % ACTIVE_FRAMES) % 6
    put(img, 6, flow_y, C_ACTIVE_DIM)
    put(img, 7, flow_y, C_ACTIVE)
    put(img, 8, flow_y, C_ACTIVE_MID)
    if flow_y + 1 <= 10:
        put(img, 7, flow_y + 1, C_ACTIVE_DIM)

    # Output port activity pulse.
    outlet = C_ACTIVE if phase % 2 == 0 else C_ACTIVE_MID
    put(img, 6, 10, outlet)
    put(img, 7, 10, C_ACTIVE)
    put(img, 8, 10, outlet)

    return img


def overlay_side_idle() -> Image.Image:
    img = blank()
    rect(img, 2, 2, 13, 13, C_DARK)
    rect(img, 3, 3, 12, 12, C_METAL)
    rect(img, 5, 4, 10, 11, C_DARK)
    rect(img, 6, 5, 9, 10, C_GLASS)

    for y in range(5, 10, 2):
        put(img, 6, y, C_LIGHT)
        put(img, 8, y, C_DARK)

    draw_pipe_column(img, 14, 4, 11)
    return img


def overlay_side_active(phase: int) -> Image.Image:
    img = overlay_side_idle()

    # Neutral fluid level in the sight glass — no recipe-specific color.
    fill_height = (phase % ACTIVE_FRAMES) + 1
    bottom = 10
    top = max(bottom - fill_height + 1, 5)
    for y in range(bottom, top - 1, -1):
        shade = C_FLUID if y % 2 == 0 else C_FLUID_BRIGHT
        put(img, 6, y, shade)
        put(img, 7, y, C_ACTIVE if y == top else shade)
        put(img, 8, y, tint(shade, -12))

    if top >= 5:
        put(img, 7, top, C_ACTIVE)
        put(img, 6, top, C_FLUID_BRIGHT)
        put(img, 8, top, C_FLUID_BRIGHT)

    return img


def overlay_top_idle() -> Image.Image:
    img = blank()
    rect(img, 3, 3, 12, 12, C_DARK)
    rect(img, 4, 4, 11, 11, C_METAL)

    for x in range(4, 12, 2):
        for y in range(4, 12, 2):
            put(img, x, y, C_LIGHT)

    rect(img, 6, 6, 9, 9, C_DARK)
    rect(img, 7, 7, 8, 8, C_GLASS)
    return img


def overlay_top_active(phase: int) -> Image.Image:
    img = overlay_top_idle()
    cx, cy = 7, 7

    # Grayscale activity ring — same idea as GT centrifuge, recipe-agnostic.
    ring_radius = 1 + (phase % 4)
    for x in range(4, 12):
        for y in range(4, 12):
            dist = abs(x - cx) + abs(y - cy)
            if dist == ring_radius:
                put(img, x, y, C_ACTIVE if (x + phase) % 2 == 0 else C_ACTIVE_MID)
            elif dist == ring_radius - 1 and ring_radius > 1:
                put(img, x, y, C_ACTIVE_DIM)

    core_glow = [C_ACTIVE_DIM, C_ACTIVE_MID, C_ACTIVE, C_HILITE, C_ACTIVE, C_ACTIVE_MID, C_ACTIVE_DIM, C_METAL][
        phase % ACTIVE_FRAMES
    ]
    put(img, cx, cy, core_glow)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        put(img, cx + dx, cy + dy, tint(core_glow, -20))

    return img


def overlay_back_idle() -> Image.Image:
    ref = REF / "overlay_back.png"
    if ref.exists():
        return Image.open(ref).convert("RGBA")
    return blank()


def save(name: str, image: Image.Image, meta: str | None = None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / name)
    meta_path = OUT / f"{name}.mcmeta"
    if meta is not None:
        meta_path.write_text(meta, encoding="utf-8")
    elif meta_path.exists():
        meta_path.unlink()


def main() -> None:
    save("overlay_front.png", overlay_front_idle())
    save(
        "overlay_front_active.png",
        frame_sheet([overlay_front_active(i) for i in range(ACTIVE_FRAMES)]),
        ACTIVE_META,
    )

    save("overlay_side.png", overlay_side_idle())
    save(
        "overlay_side_active.png",
        frame_sheet([overlay_side_active(i) for i in range(ACTIVE_FRAMES)]),
        ACTIVE_META,
    )

    save("overlay_top.png", overlay_top_idle())
    save(
        "overlay_top_active.png",
        frame_sheet([overlay_top_active(i) for i in range(ACTIVE_FRAMES)]),
        ACTIVE_META,
    )

    # GT keeps the back overlay static while working.
    save("overlay_back.png", overlay_back_idle())
    save("overlay_back_active.png", overlay_back_idle())

    print(f"Generated machine overlays in {OUT}")


if __name__ == "__main__":
    main()
