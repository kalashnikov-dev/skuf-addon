package com.arturgpt.skufaddon.common.data;

import com.arturgpt.skufaddon.SkufAddon;

import com.gregtechceu.gtceu.api.data.tag.TagPrefix;
import com.gregtechceu.gtceu.common.data.GTMaterialBlocks;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.material.MapColor;

import com.tterrag.registrate.util.entry.BlockEntry;

/**
 * GT material block helpers for multiblock structures.
 */
public final class SkufBlocks {

    public static BlockEntry<Block> BROKEN_MONITOR_BLOCK;
    public static BlockEntry<Block> CASING_POHUIT_REINFORCED;
    public static BlockEntry<Block> CASING_PROVAL_CONCRETE;

    private SkufBlocks() {}

    public static void init() {
        BROKEN_MONITOR_BLOCK = SkufAddon.REGISTRATE
                .block("block_broken_monitor", Block::new)
                .properties(props -> props
                        .mapColor(MapColor.COLOR_PURPLE)
                        .sound(SoundType.GLASS)
                        .strength(0.8f, 0.8f)
                        .requiresCorrectToolForDrops())
                .simpleItem()
                .register();

        CASING_POHUIT_REINFORCED = SkufAddon.REGISTRATE
                .block("casing_pohuit_reinforced", Block::new)
                .properties(props -> props
                        .mapColor(MapColor.COLOR_GRAY)
                        .sound(SoundType.METAL)
                        .strength(5.0f, 6.0f)
                        .requiresCorrectToolForDrops())
                .simpleItem()
                .register();

        CASING_PROVAL_CONCRETE = SkufAddon.REGISTRATE
                .block("casing_proval_concrete", Block::new)
                .properties(props -> props
                        .mapColor(MapColor.STONE)
                        .sound(SoundType.STONE)
                        .strength(4.0f, 5.0f)
                        .requiresCorrectToolForDrops())
                .simpleItem()
                .register();
    }

    @SuppressWarnings("unchecked")
    public static BlockEntry<Block> skufitFrame() {
        return (BlockEntry<Block>) GTMaterialBlocks.MATERIAL_BLOCKS.get(TagPrefix.frameGt, SkufMaterials.skufit);
    }

    @SuppressWarnings("unchecked")
    public static BlockEntry<Block> pokhuitFrame() {
        return (BlockEntry<Block>) GTMaterialBlocks.MATERIAL_BLOCKS.get(TagPrefix.frameGt, SkufMaterials.pokhuit);
    }

    @SuppressWarnings("unchecked")
    public static BlockEntry<Block> correctMatterBlock() {
        return (BlockEntry<Block>) GTMaterialBlocks.MATERIAL_BLOCKS.get(TagPrefix.block, SkufMaterials.correctMatter);
    }

    public static BlockEntry<Block> brokenMonitorBlock() {
        return BROKEN_MONITOR_BLOCK;
    }
}
