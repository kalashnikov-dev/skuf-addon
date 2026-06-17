from pathlib import Path

import cv2
import numpy as np
from PIL import Image

VIDEO = Path(r"C:\Users\daynt\Downloads\0558b0e4-eb05-4fd6-a99a-1523ddedeba6.mp4")
OUT = Path(r"C:\Users\daynt\IdeaProjects\skuf-addon\src\main\resources\assets\skufaddon\textures\item")

BG = np.array([29, 30, 35], dtype=np.int16)
BG_KEY_COLORS = (
    (29, 30, 35),
    (28, 28, 36),
    (28, 28, 38),
    (26, 29, 36),
    (28, 29, 34),
    (30, 28, 36),
    (46, 49, 58),
)
BG_TOLERANCE = 8
FRAME_SIZE = 16
FRAME_COUNT = 8
FRAME_TIME = 3  # ~7.7 fps in the reference video


def remove_background(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue

            for bg_red, bg_green, bg_blue in BG_KEY_COLORS:
                if (
                    abs(red - bg_red) <= BG_TOLERANCE
                    and abs(green - bg_green) <= BG_TOLERANCE
                    and abs(blue - bg_blue) <= BG_TOLERANCE
                ):
                    pixels[x, y] = (0, 0, 0, 0)
                    break

    return rgba


def crop_box(region: np.ndarray) -> tuple[int, int, int, int]:
    mask = np.any(np.abs(region.astype(np.int16) - BG) > 8, axis=2)
    ys, xs = np.where(mask)
    cx = (xs.min() + xs.max()) // 2
    cy = (ys.min() + ys.max()) // 2
    size = max(xs.max() - xs.min(), ys.max() - ys.min()) + 8
    size = size + (size % 2)
    half = size // 2
    y0 = max(0, cy - half)
    x0 = max(0, cx - half)
    y1 = min(region.shape[0], y0 + size)
    x1 = min(region.shape[1], x0 + size)
    return x0, y0, x1, y1


def extract_side(frames: list[np.ndarray], x_start: int, x_end: int) -> list[Image.Image]:
    region0 = frames[0][:, x_start:x_end]
    x0, y0, x1, y1 = crop_box(region0)
    extracted: list[Image.Image] = []

    for frame in frames:
        region = frame[:, x_start:x_end]
        crop = region[y0:y1, x0:x1]
        frame = Image.fromarray(crop).resize((FRAME_SIZE, FRAME_SIZE), Image.NEAREST)
        extracted.append(remove_background(frame))

    return extracted


def save_sheet(name: str, frames: list[Image.Image]) -> None:
    sheet = Image.new("RGBA", (FRAME_SIZE, FRAME_SIZE * len(frames)), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        sheet.paste(frame.convert("RGBA"), (0, index * FRAME_SIZE))

    png_path = OUT / f"{name}.png"
    meta_path = OUT / f"{name}.png.mcmeta"
    sheet.save(png_path)

    meta = (
        "{\n"
        "  \"animation\": {\n"
        f"    \"frametime\": {FRAME_TIME},\n"
        f"    \"width\": {FRAME_SIZE},\n"
        f"    \"height\": {FRAME_SIZE},\n"
        "    \"interpolate\": false\n"
        "  }\n"
        "}\n"
    )
    meta_path.write_text(meta, encoding="utf-8")
    print(f"{name}: {png_path} -> {sheet.size}")


def load_video_frames() -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(VIDEO))
    frames: list[np.ndarray] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    return frames


def main() -> None:
    frames = load_video_frames()
    if len(frames) != FRAME_COUNT:
        raise RuntimeError(f"Expected {FRAME_COUNT} frames, got {len(frames)}")

    width = frames[0].shape[1]
    mid = width // 2

    save_sheet("pravilnaya_vesh", extract_side(frames, 0, mid))
    save_sheet("pukan_core", extract_side(frames, mid, width))


if __name__ == "__main__":
    main()
