package com.arturgpt.skufaddon.common.data;

import com.gregtechceu.gtceu.api.data.tag.TagPrefix;
import com.gregtechceu.gtceu.common.data.GTMaterialBlocks;

import net.minecraft.world.level.block.Block;

import com.tterrag.registrate.util.entry.BlockEntry;

/**
 * GT material block helpers for multiblock structures.
 */
public final class SkufBlocks {

    private SkufBlocks() {}

    public static void init() {}

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
}
