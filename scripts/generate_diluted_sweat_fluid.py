"""Diluted sweat uses the same GT liquid template as sweat (no custom PNG).

Tint is set in SkufMaterials.dilutedSweat via FluidBuilder.color():
  - sweat:        0xD4C84A (procedural tint on gtceu:block/material_sets/fluid/liquid)
  - diluted:      0xA8E0D880 (lighter yellow, ~66% alpha)

GT fluid still textures are 16x512 strips — a 16x16 custom PNG will render incorrectly.
"""

from __future__ import annotations


def main() -> None:
    print("diluted sweat: procedural GT tint in SkufMaterials.java (no asset generation)")


if __name__ == "__main__":
    main()
