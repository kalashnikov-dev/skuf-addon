---
trigger: always
description: "Key development lessons learned for Minecraft GTCEu Modern addon development and FTB Quests configuration"
---

# Lessons Learned: SkufAddon & FTB Quests Development

## 1. Exact Item & Block ID Resolution (Never Guess Names)
- **Always inspect Java registration files**: Inspect `SkufMaterials.java`, `SkufBlocks.java`, `SkufItems.java`, `SkufSingleblockMachines.java`, `SkufComponentMachines.java`, and `SkufMultiblockMachines.java` before referencing item/block/machine IDs.
- **GTCEu Material Dust Suffixes**: Material IDs containing words like `normie_dust` in `Material.Builder(SkufAddon.id("normie_dust")).dust()` generate `skufaddon:normie_dust_dust` because GTCEu automatically appends `_dust`.
- **Block Registrate Prefixes**: Blocks like `BROKEN_MONITOR_BLOCK` may be registered as `block_broken_monitor` (`skufaddon:block_broken_monitor`).
- **Tiered Machine Naming**: Singleblock tiered machines use `GTValues.VN[tier].toLowerCase() + "_" + baseName` (e.g., `lv_cnc_machine`, `lv_normis_filtration_machine`, `lv_pot_distillery`).

## 2. Namespace Rule for GTCEu Addon Materials
- GTCEu material items generated from custom addon materials defined with `SkufAddon.id("...")` are registered under the **addon's namespace (`skufaddon:`)**, NOT `gtceu:`.

## 3. FTB Quests 1.20.1 Signed Long ID Constraint
- FTB Quests reads hexadecimal quest, task, and link IDs using Java's `Long.parseLong(id, 16)`.
- `Long.parseLong` in Java parses a signed 64-bit Long (max `0x7FFFFFFFFFFFFFFF`).
- Any 16-character hex string starting with `8`..`F` throws a `NumberFormatException` when loading server/world data.
- **Fix**: Mask generated hex integer values with `& 0x7FFFFFFFFFFFFFFF` so IDs always fit positive signed Longs.

## 4. Fluid Icons in FTB Quests
- Fluid tasks (`type: "fluid"`) lack default item icon renders in FTB Quests.
- Always specify the GTCEu fluid bucket item (`skufaddon:<fluid_name>_bucket`) as the quest's `icon`.

## 5. Chapter Header & Tab Grouping
- In FTB Quests, set `group: ""` on chapters to display chapter titles directly on tab header buttons without "Unnamed" header overrides.
