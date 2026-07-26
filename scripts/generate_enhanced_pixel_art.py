#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate enhanced 16x16 pixel art textures for SkufAddon:
1. Animated Vibe Singularity (16x128 8-frame PNG + mcmeta)
2. Industrial Proval Concrete Casing (16x16 PNG)
3. Tier-differentiated Dodik Circuits (1, 2, 3) (16x16 PNGs)
4. CRT Broken Monitor Block (16x16 PNG)
5. Custom Fluid Bucket Textures (Sweat, Jizhnyak, Tears, Coolant, Dense Jizhnyak, Vibe) (16x16 PNGs)
"""

import os, math, json
from PIL import Image, ImageDraw

ITEM_DIR = r"E:\Users\fast1\Desktop\real_projects\skuf-addon\src\main\resources\assets\skufaddon\textures\item"
BLOCK_DIR = r"E:\Users\fast1\Desktop\real_projects\skuf-addon\src\main\resources\assets\skufaddon\textures\block"

os.makedirs(ITEM_DIR, exist_ok=True)
os.makedirs(BLOCK_DIR, exist_ok=True)

# Helper to build iron bucket base
def draw_iron_bucket():
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    
    # Outer dark iron border
    border_pixels = [
        (4,3), (5,3), (10,3), (11,3),
        (3,4), (12,4),
        (3,5), (12,5),
        (3,6), (12,6),
        (4,7), (11,7),
        (4,8), (11,8),
        (4,9), (11,9),
        (5,10), (10,10),
        (5,11), (10,11),
        (5,12), (10,12),
        (6,13), (7,13), (8,13), (9,13)
    ]
    for x, y in border_pixels:
        d.point((x, y), fill=(35, 38, 42, 255))
        
    # Metal handle arch
    handle_pixels = [
        (4,2), (5,1), (6,1), (7,1), (8,1), (9,1), (10,1), (11,2)
    ]
    for x, y in handle_pixels:
        d.point((x, y), fill=(100, 105, 115, 255))
        
    # Bucket body metal shading
    for y in range(5, 13):
        x_min = 4 if y in (5,6,7,8,9) else 5 if y in (10,11,12) else 6
        x_max = 11 if y in (5,6,7,8,9) else 10 if y in (10,11,12) else 9
        for x in range(x_min, x_max + 1):
            if x == x_min:
                color = (130, 135, 145, 255) # Highlight edge
            elif x == x_min + 1:
                color = (170, 175, 185, 255) # Bright specular
            elif x in (x_max - 1, x_max):
                color = (60, 65, 75, 255)   # Shadow
            else:
                color = (100, 105, 115, 255) # Base metal
            d.point((x, y), fill=color)
            
    return im

def draw_fluid_in_bucket(base_bucket, fluid_rgb_dark, fluid_rgb_mid, fluid_rgb_light):
    im = base_bucket.copy()
    d = ImageDraw.Draw(im)
    
    # Fluid surface (y=5,6)
    fluid_pixels = [
        (4,5, fluid_rgb_light), (5,5, fluid_rgb_light), (6,5, fluid_rgb_mid), (7,5, fluid_rgb_mid),
        (8,5, fluid_rgb_dark), (9,5, fluid_rgb_dark), (10,5, fluid_rgb_dark), (11,5, fluid_rgb_dark),
        (4,6, fluid_rgb_mid), (5,6, fluid_rgb_light), (6,6, fluid_rgb_mid), (7,6, fluid_rgb_mid),
        (8,6, fluid_rgb_dark), (9,6, fluid_rgb_dark), (10,6, fluid_rgb_dark), (11,6, fluid_rgb_dark)
    ]
    for x, y, col in fluid_pixels:
        d.point((x, y), fill=(col[0], col[1], col[2], 255))
        
    return im

# ---------------------------------------------------------------------------
# 1. ANIMATED VIBE SINGULARITY (16x128 8 frames)
# ---------------------------------------------------------------------------
def gen_vibe_singularity():
    frames = []
    for f in range(8):
        im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        angle_offset = (f / 8.0) * math.pi * 2
        pulse = (math.sin(angle_offset) + 1.0) / 2.0 # 0.0 .. 1.0
        
        cx, cy = 7.5, 7.5
        for y in range(16):
            for x in range(16):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                if dist < 2.2 + pulse * 0.4:
                    # Core
                    c = int(220 + pulse * 35)
                    d.point((x, y), fill=(c, 255, 240, 255))
                elif dist < 4.2:
                    # Inner aura
                    alpha = int((1.0 - (dist - 2.2)/2.0) * 220)
                    d.point((x, y), fill=(40, 200, 220, alpha))
                elif dist < 6.5:
                    # Outer energy ring
                    a = math.atan2(y - cy, x - cx)
                    spin = (a + angle_offset) % (math.pi / 2)
                    if spin < 0.6:
                        alpha = int((1.0 - (dist - 4.2)/2.3) * 160)
                        d.point((x, y), fill=(100, 100, 255, alpha))
        frames.append(im)
        
    strip = Image.new("RGBA", (16, 128))
    for i, frame in enumerate(frames):
        strip.paste(frame, (0, i * 16))
    
    strip_path = os.path.join(ITEM_DIR, "vibe_singularity.png")
    strip.save(strip_path)
    
    mcmeta_path = os.path.join(ITEM_DIR, "vibe_singularity.png.mcmeta")
    with open(mcmeta_path, "w", encoding="utf-8") as f:
        json.dump({"animation": {"frametime": 2, "interpolate": True}}, f, indent=2)
    print("Generated: vibe_singularity.png + mcmeta")

# ---------------------------------------------------------------------------
# 2. INDUSTRIAL PROVAL CONCRETE CASING (16x16)
# ---------------------------------------------------------------------------
def gen_proval_concrete():
    im = Image.new("RGBA", (16, 16), (60, 65, 70, 255))
    d = ImageDraw.Draw(im)
    
    # Outer dark steel frame border
    for i in range(16):
        d.point((i, 0), fill=(30, 32, 35, 255))
        d.point((i, 15), fill=(30, 32, 35, 255))
        d.point((0, i), fill=(30, 32, 35, 255))
        d.point((15, i), fill=(30, 32, 35, 255))
        
    # Bevel highlight & shadow
    for i in range(1, 15):
        d.point((i, 1), fill=(90, 95, 105, 255))
        d.point((1, i), fill=(90, 95, 105, 255))
        d.point((i, 14), fill=(40, 43, 48, 255))
        d.point((14, i), fill=(40, 43, 48, 255))

    # Concrete inner texture with noise and rusted rebar bolts in corners
    for y in range(2, 14):
        for x in range(2, 14):
            # Base stone noise
            val = 65 + ((x * 7 + y * 13) % 15)
            d.point((x, y), fill=(val, val + 5, val + 8, 255))
            
    # Corner rusty rivets/bolts
    bolts = [(3,3), (12,3), (3,12), (12,12)]
    for bx, by in bolts:
        d.point((bx, by), fill=(160, 80, 40, 255)) # Rust orange
        d.point((bx+1, by), fill=(40, 20, 10, 255))
        
    # Micro crack lines
    cracks = [(5,6), (6,6), (7,7), (8,8), (9,8)]
    for cx, cy in cracks:
        d.point((cx, cy), fill=(35, 38, 42, 255))
        
    p_path = os.path.join(BLOCK_DIR, "casing_proval_concrete.png")
    im.save(p_path)
    item_p_path = os.path.join(ITEM_DIR, "casing_proval_concrete.png")
    im.save(item_p_path)
    print("Generated: casing_proval_concrete.png")

# ---------------------------------------------------------------------------
# 3. DODIK CIRCUITS (1, 2, 3)
# ---------------------------------------------------------------------------
def gen_dodik_circuits():
    # Circuit 1 (LV - Green PCB + Copper traces)
    c1 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d1 = ImageDraw.Draw(c1)
    # Green PCB board
    for y in range(3, 13):
        for x in range(3, 13):
            d1.point((x, y), fill=(20, 100, 40, 255))
    # Border
    for i in range(3, 13):
        d1.point((i, 3), fill=(10, 60, 25, 255))
        d1.point((i, 12), fill=(10, 60, 25, 255))
        d1.point((3, i), fill=(10, 60, 25, 255))
        d1.point((12, i), fill=(10, 60, 25, 255))
    # Copper traces & Chip
    for x in range(5, 11): d1.point((x, 7), fill=(200, 120, 40, 255))
    for y in range(5, 11): d1.point((7, y), fill=(200, 120, 40, 255))
    # IC Chip
    for cy in range(6, 9):
        for cx in range(6, 9):
            d1.point((cx, cy), fill=(40, 40, 45, 255))
    c1.save(os.path.join(ITEM_DIR, "dodik_circuit_1.png"))

    # Circuit 2 (MV - Blue PCB + Gold buses)
    c2 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(c2)
    for y in range(2, 14):
        for x in range(2, 14):
            d2.point((x, y), fill=(20, 60, 120, 255))
    for i in range(2, 14):
        d2.point((i, 2), fill=(10, 35, 70, 255))
        d2.point((i, 13), fill=(10, 35, 70, 255))
        d2.point((2, i), fill=(10, 35, 70, 255))
        d2.point((13, i), fill=(10, 35, 70, 255))
    # Gold buses
    for x in range(4, 12):
        d2.point((x, 5), fill=(240, 190, 50, 255))
        d2.point((x, 10), fill=(240, 190, 50, 255))
    # Dual IC Chips
    for cy in range(6, 9):
        for cx in range(4, 7): d2.point((cx, cy), fill=(30, 30, 35, 255))
        for cx in range(9, 12): d2.point((cx, cy), fill=(30, 30, 35, 255))
    c2.save(os.path.join(ITEM_DIR, "dodik_circuit_2.png"))

    # Circuit 3 (HV - Purple PCB + Mainframe Core)
    c3 = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d3 = ImageDraw.Draw(c3)
    for y in range(2, 14):
        for x in range(2, 14):
            d3.point((x, y), fill=(80, 20, 100, 255))
    for i in range(2, 14):
        d3.point((i, 2), fill=(40, 10, 55, 255))
        d3.point((i, 13), fill=(40, 10, 55, 255))
        d3.point((2, i), fill=(40, 10, 55, 255))
        d3.point((13, i), fill=(40, 10, 55, 255))
    # Center heat sink
    for cy in range(5, 11):
        for cx in range(5, 11):
            d3.point((cx, cy), fill=(160, 165, 175, 255))
    for cy in range(6, 10):
        for cx in range(6, 10):
            d3.point((cx, cy), fill=(180, 50, 220, 255)) # Purple core
    c3.save(os.path.join(ITEM_DIR, "dodik_circuit_3.png"))
    print("Generated: dodik_circuit_1.png, 2.png, 3.png")

# ---------------------------------------------------------------------------
# 4. CRT BROKEN MONITOR BLOCK (16x16)
# ---------------------------------------------------------------------------
def gen_broken_monitor():
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    
    # Outer dark casing
    for y in range(16):
        for x in range(16):
            d.point((x, y), fill=(40, 42, 48, 255))
            
    # Bevel
    for i in range(1, 15):
        d.point((i, 1), fill=(70, 75, 85, 255))
        d.point((1, i), fill=(70, 75, 85, 255))
        d.point((i, 14), fill=(25, 27, 30, 255))
        d.point((14, i), fill=(25, 27, 30, 255))
        
    # CRT Screen area (2,2 to 13,13)
    for y in range(2, 14):
        for x in range(2, 14):
            d.point((x, y), fill=(15, 20, 25, 255)) # Dark glass
            
    # Glass crack lines & magenta error static glow
    cracks = [
        (3,4), (4,5), (5,6), (6,7), (7,8), (8,7), (9,6), (10,5), (11,4),
        (7,9), (7,10), (8,11), (9,12), (6,10), (5,11)
    ]
    for cx, cy in cracks:
        d.point((cx, cy), fill=(220, 230, 255, 255)) # Glass highlight crack
    
    # Purple/magenta error static behind crack
    d.point((6,8), fill=(255, 40, 180, 255))
    d.point((7,7), fill=(0, 240, 220, 255))
    d.point((8,8), fill=(255, 40, 180, 255))
    
    b_path = os.path.join(BLOCK_DIR, "block_broken_monitor.png")
    im.save(b_path)
    item_b_path = os.path.join(ITEM_DIR, "block_broken_monitor.png")
    im.save(item_b_path)
    print("Generated: block_broken_monitor.png")

# ---------------------------------------------------------------------------
# 5. FLUID BUCKETS
# ---------------------------------------------------------------------------
def gen_fluid_buckets():
    base = draw_iron_bucket()
    
    buckets = [
        ("sweat_bucket.png", (220, 200, 60), (190, 170, 40), (140, 120, 20)),
        ("jizhnyak_bucket.png", (110, 110, 70), (95, 95, 60), (70, 70, 40)),
        ("technical_tears_bucket.png", (90, 160, 220), (70, 130, 190), (50, 90, 150)),
        ("coolant_of_denial_bucket.png", (60, 220, 230), (45, 180, 200), (30, 130, 150)),
        ("dense_jizhnyak_bucket.png", (70, 100, 50), (55, 80, 40), (40, 60, 30)),
        ("stabilized_vibe_bucket.png", (70, 230, 210), (50, 190, 180), (30, 140, 130)),
        ("zhizhnyak_loss_bucket.png", (70, 65, 50), (60, 55, 40), (45, 40, 30)),
        ("ugar_gas_bucket.png", (200, 100, 40), (170, 80, 30), (130, 50, 20)),
        ("hidden_sweat_bucket.png", (200, 180, 50), (170, 150, 40), (130, 110, 30)),
        ("condensed_sweat_bucket.png", (240, 220, 70), (210, 190, 50), (170, 150, 30)),
        ("diluted_sweat_bucket.png", (230, 220, 140), (200, 190, 110), (160, 150, 80)),
        ("warm_vibe_steam_bucket.png", (210, 190, 150), (180, 160, 120), (140, 120, 90)),
        ("padik_noble_gas_bucket.png", (120, 100, 150), (90, 75, 120), (60, 50, 90)),
        ("puff_smoke_bucket.png", (60, 60, 65), (45, 45, 50), (30, 30, 35))
    ]
    
    for filename, light, mid, dark in buckets:
        bucket_im = draw_fluid_in_bucket(base, dark, mid, light)
        bucket_im.save(os.path.join(ITEM_DIR, filename))
        
    print("Generated: 14 fluid bucket item textures!")

if __name__ == "__main__":
    gen_vibe_singularity()
    gen_proval_concrete()
    gen_dodik_circuits()
    gen_broken_monitor()
    gen_fluid_buckets()
