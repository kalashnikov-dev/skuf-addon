"""Generate only the broken monitor block texture."""
from pathlib import Path

from PIL import Image

RES = Path(__file__).resolve().parents[1] / "src/main/resources/assets/skufaddon/textures/block"


def make_broken_monitor_block_texture() -> None:
    """Cracked dark monitor screen — block form only."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    bezel = (0x1A, 0x1A, 0x28, 255)
    bezel_hi = (0x3A, 0x3A, 0x50, 255)
    screen = (0x22, 0x22, 0x44, 255)
    screen_hi = (0x32, 0x32, 0x66, 255)
    crack = (0x0A, 0x0A, 0x12, 255)
    glitch = (0x4A, 0x60, 0x90, 255)
    dead_pixel = (0x10, 0x10, 0x18, 255)

    for x in range(16):
        for y in range(16):
            px[x, y] = bezel

    for x in range(2, 14):
        for y in range(2, 13):
            px[x, y] = screen
    for x in range(3, 13):
        px[x, 3] = screen_hi
    for y in range(3, 12):
        px[3, y] = screen_hi

    # Crack lines
    crack_pts = [
        (7, 4), (8, 5), (9, 6), (10, 7), (11, 8), (10, 9), (9, 10), (8, 9),
        (7, 8), (6, 7), (7, 6), (8, 7),
        (5, 5), (6, 6), (5, 7),
        (11, 4), (10, 5),
    ]
    for x, y in crack_pts:
        px[x, y] = crack

    # Glitch artifacts / broken pixels
    for x, y in [(5, 8), (11, 6), (6, 10), (12, 9), (4, 6)]:
        px[x, y] = glitch
    for x, y in [(8, 4), (9, 11), (5, 9)]:
        px[x, y] = dead_pixel

    # Stand
    for x in range(6, 10):
        px[x, 13] = bezel_hi
    for x in range(7, 9):
        px[x, 14] = bezel
        px[x, 15] = bezel

    out = RES / "block_broken_monitor.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


if __name__ == "__main__":
    make_broken_monitor_block_texture()
    print("Generated block_broken_monitor.png only.")
