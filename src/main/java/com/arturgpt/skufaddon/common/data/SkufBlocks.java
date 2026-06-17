package com.arturgpt.skufaddon.common.data;

import com.arturgpt.skufaddon.SkufAddon;

import com.gregtechceu.gtceu.api.data.tag.TagPrefix;
import com.gregtechceu.gtceu.common.data.GTMaterialBlocks;

import net.minecraft.world.level.block.Block;

import com.tterrag.registrate.util.entry.BlockEntry;

/**
 * Custom multiblock structure blocks and GT material frame helpers.
 */
public final class SkufBlocks {

    public static BlockEntry<Block> PUKAN_CORE_CASING;

    private SkufBlocks() {}

    public static void init() {
        PUKAN_CORE_CASING = SkufAddon.REGISTRATE
                .block("pukan_core_casing", props -> new Block(props))
                .properties(p -> p.strength(5.0f, 10.0f).requiresCorrectToolForDrops())
                .lang("Pukan Core Casing")
                .blockstate((ctx, prov) -> prov.simpleBlock(ctx.get()))
                .item()
                .model((ctx, prov) -> prov.withExistingParent(ctx.getName(), SkufAddon.id("block/pukan_core_casing")))
                .build()
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
}
