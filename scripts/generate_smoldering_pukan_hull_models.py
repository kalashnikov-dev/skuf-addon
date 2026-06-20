"""Generate gtceu:machine JSON assets for tiered Smoldering Pukan hull blocks."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "src" / "main" / "resources" / "assets" / "skufaddon"

TIERS = ("lv", "mv", "hv", "ev", "iv", "luv", "zpm", "uv", "uhv")


def blockstate(machine: str) -> dict:
    model = f"skufaddon:block/machine/{machine}"
    return {
        "variants": {
            "facing=down": {"model": model, "x": 90},
            "facing=east": {"model": model, "y": 90},
            "facing=north": {"model": model},
            "facing=south": {"model": model, "y": 180},
            "facing=up": {"gtceu:z": 180, "model": model, "x": 270},
            "facing=west": {"model": model, "y": 270},
        }
    }


def casing_variant(tier: str) -> dict:
    return {
        "parent": "skufaddon:block/machine/part/smoldering_pukan",
        "textures": {
            "bottom": f"gtceu:block/casings/voltage/{tier}/bottom",
            "side": f"gtceu:block/casings/voltage/{tier}/side",
            "top": f"gtceu:block/casings/voltage/{tier}/top",
        },
    }


def machine_model(machine: str, tier: str) -> dict:
    variant = casing_variant(tier)
    return {
        "parent": "minecraft:block/block",
        "loader": "gtceu:machine",
        "machine": f"skufaddon:{machine}",
        "replaceable_textures": ["bottom", "top", "side"],
        "variants": {
            "is_formed=false": {"model": variant},
            "is_formed=true": {"model": variant},
        },
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for tier in TIERS:
        machine = f"{tier}_smoldering_pukan"
        write_json(RES / "blockstates" / f"{machine}.json", blockstate(machine))
        write_json(RES / "models" / "block" / "machine" / f"{machine}.json", machine_model(machine, tier))
        write_json(RES / "models" / "item" / f"{machine}.json", {"parent": f"skufaddon:block/machine/{machine}"})
        print(f"  {machine}")

    print(f"Done — {len(TIERS)} hull model sets")


if __name__ == "__main__":
    main()
