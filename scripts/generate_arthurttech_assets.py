"""Generate procedural textures and JSON models for ArthurTech content."""
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

MOD = "skufaddon"
TIERS = ("lv", "mv", "hv", "ev", "iv", "luv", "zpm", "uv", "uhv")
RES = Path(r"C:\Users\daynt\IdeaProjects\skuf-addon\src\main\resources\assets\skufaddon")

ITEM_COLORS = {
    "cnc_bit": 0x9AA4AD,
    "cnc_cutter": 0x8A949D,
    "pukan_indicator_core": 0x66FF33,
    "melted_capacitor": 0xB85C1E,
    "burnt_cable_debris": 0x2A2A2A,
    "charred_developer_circuit": 0x4A4038,
    "myposhko_script": 0x4F7FB5,
    "egor_core": 0xC9B98F,
    "correct_matter_microcapsule": 0x36C9B0,
    "antizoomer_core": 0x6B5E8C,
    "correct_developer_schematic": 0x49E0D0,
    "normis_singularity": 0x8A8A8A,
    "absolute_pohuit": 0x3A7A5C,
    "arturian_mainframe": 0x7A5C3A,
}

TILT_MACHINES = ("cnc_machine", "pot_distillery", "vibe_stabilizer")

MULTIBLOCK_ITEMS = (
    "mini_factory",
    "chelyabinsk_proval",
    "sauna_egora",
    "skufizator",
)

BLOCKSTATE = """{{
  "variants": {{
    "facing=east": {{
      "model": "{mod}:block/machine/{machine}",
      "y": 90
    }},
    "facing=north": {{
      "model": "{mod}:block/machine/{machine}"
    }},
    "facing=south": {{
      "model": "{mod}:block/machine/{machine}",
      "y": 180
    }},
    "facing=west": {{
      "model": "{mod}:block/machine/{machine}",
      "y": 270
    }}
  }}
}}
"""

ITEM_MODEL = """{{
  "parent": "{mod}:block/machine/{machine}"
}}
"""


def rgb(color: int) -> tuple[int, int, int]:
    return ((color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF)


def make_item_texture(name: str, color: int) -> None:
    base = rgb(color)
    dark = tuple(max(0, c - 50) for c in base)
    light = tuple(min(255, c + 40) for c in base)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle((4, 2, 11, 13), fill=(*dark, 255))
    draw.rectangle((5, 3, 10, 12), fill=(*base, 255))
    draw.line((5, 3, 5, 12), fill=(*light, 255))
    draw.rectangle((7, 1, 8, 3), fill=(*light, 255))
    out = RES / "textures" / "item" / f"{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


def make_block_texture(name: str, color: int) -> None:
    base = rgb(color)
    dark = tuple(max(0, c - 35) for c in base)
    light = tuple(min(255, c + 35) for c in base)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            tone = dark if (x + y) % 4 == 0 else base
            if x == 0 or y == 0:
                tone = light
            if x == 15 or y == 15:
                tone = dark
            img.putpixel((x, y), (*tone, 255))
    out = RES / "textures" / "block" / f"{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


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


def write_block_model(name: str) -> None:
    path = RES / "models" / "block" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "parent": "minecraft:block/cube_all",
                "textures": {"all": f"{MOD}:block/{name}"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_blockstate(name: str) -> None:
    path = RES / "blockstates" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"variants": {"": {"model": f"{MOD}:block/{name}"}}}, indent=2) + "\n",
        encoding="utf-8",
    )


def overlay_textures(overlay_base: str, active: bool) -> dict[str, str]:
    suffix = "_active" if active else ""
    return {
        "overlay_back": f"{overlay_base}/overlay_back{suffix}",
        "overlay_front": f"{overlay_base}/overlay_front{suffix}",
        "overlay_side": f"{overlay_base}/overlay_side{suffix}",
        "overlay_top": f"{overlay_base}/overlay_top{suffix}",
    }


def machine_model(tier: str, machine: str, overlay_base: str) -> dict:
    casing = f"gtceu:block/casings/voltage/{tier}"
    variants = {}
    for status, active in (
        ("idle", False),
        ("suspend", False),
        ("waiting", True),
        ("working", True),
    ):
        variants[f"recipe_logic_status={status}"] = {
            "model": {
                "parent": casing,
                "textures": overlay_textures(overlay_base, active),
            }
        }
    return {
        "parent": "minecraft:block/block",
        "loader": "gtceu:machine",
        "machine": f"{MOD}:{machine}",
        "variants": variants,
    }


def copy_normis_overlay(machine: str) -> None:
    src = RES / "textures" / "block" / "machines" / "normis_filtration_machine"
    dst = RES / "textures" / "block" / "machines" / machine
    dst.mkdir(parents=True, exist_ok=True)
    for file in src.iterdir():
        if file.is_file():
            shutil.copy2(file, dst / file.name)


def write_tilt_machine_assets(machine_base: str) -> None:
    copy_normis_overlay(machine_base)
    overlay_base = f"{MOD}:block/machines/{machine_base}"

    for tier in TIERS:
        machine = f"{tier}_{machine_base}"

        (RES / "blockstates" / f"{machine}.json").write_text(
            BLOCKSTATE.format(mod=MOD, machine=machine),
            encoding="utf-8",
        )

        block_model_path = RES / "models" / "block" / "machine" / f"{machine}.json"
        block_model_path.parent.mkdir(parents=True, exist_ok=True)
        block_model_path.write_text(
            json.dumps(machine_model(tier, machine, overlay_base), indent=2) + "\n",
            encoding="utf-8",
        )

        (RES / "models" / "item" / f"{machine}.json").write_text(
            ITEM_MODEL.format(mod=MOD, machine=machine),
            encoding="utf-8",
        )


def write_multiblock_item_models() -> None:
    frame_model = "gtceu:block/material_sets/shiny/frame_gt"
    for name in MULTIBLOCK_ITEMS:
        if name == "skufizator":
            continue
        path = RES / "models" / "item" / f"{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"parent": frame_model}, indent=2) + "\n",
            encoding="utf-8",
        )


def main() -> None:
    for name, color in ITEM_COLORS.items():
        make_item_texture(name, color)
        write_item_model(name)

    for machine in TILT_MACHINES:
        write_tilt_machine_assets(machine)

    write_multiblock_item_models()
    print("Generated ArthurTech assets.")


if __name__ == "__main__":
    main()
