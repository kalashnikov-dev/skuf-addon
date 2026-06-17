import json
from pathlib import Path

MOD = "skufaddon"
TIERS = ("lv", "mv", "hv", "ev", "iv", "luv", "zpm", "uv", "uhv")
OVERLAY = f"{MOD}:block/machines/normis_filtration_machine"
RES = Path(r"C:\Users\daynt\IdeaProjects\skuf-addon\src\main\resources\assets\skufaddon")

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


def overlay_textures(active: bool) -> dict[str, str]:
    suffix = "_active" if active else ""
    return {
        "overlay_back": f"{OVERLAY}/overlay_back{suffix}",
        "overlay_front": f"{OVERLAY}/overlay_front{suffix}",
        "overlay_side": f"{OVERLAY}/overlay_side{suffix}",
        "overlay_top": f"{OVERLAY}/overlay_top{suffix}",
    }


def machine_model(tier: str, machine: str) -> dict:
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
                "textures": overlay_textures(active),
            }
        }

    return {
        "parent": "minecraft:block/block",
        "loader": "gtceu:machine",
        "machine": f"{MOD}:{machine}",
        "variants": variants,
    }


def main() -> None:
    for tier in TIERS:
        machine = f"{tier}_normis_filtration_machine"

        blockstate_path = RES / "blockstates" / f"{machine}.json"
        blockstate_path.parent.mkdir(parents=True, exist_ok=True)
        blockstate_path.write_text(
            BLOCKSTATE.format(mod=MOD, machine=machine),
            encoding="utf-8",
        )

        block_model_path = RES / "models/block/machine" / f"{machine}.json"
        block_model_path.parent.mkdir(parents=True, exist_ok=True)
        block_model_path.write_text(
            json.dumps(machine_model(tier, machine), indent=2) + "\n",
            encoding="utf-8",
        )

        item_model_path = RES / "models/item" / f"{machine}.json"
        item_model_path.parent.mkdir(parents=True, exist_ok=True)
        item_model_path.write_text(
            ITEM_MODEL.format(mod=MOD, machine=machine),
            encoding="utf-8",
        )

        print(machine)


if __name__ == "__main__":
    main()
