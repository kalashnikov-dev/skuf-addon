package com.arturgpt.skufaddon.common.data;

import com.arturgpt.skufaddon.SkufAddon;

import com.gregtechceu.gtceu.api.data.worldgen.WorldGenLayers;
import com.gregtechceu.gtceu.common.data.GTOres;

import net.minecraft.tags.BiomeTags;
import net.minecraft.util.valueproviders.UniformInt;

public class SkufOres {

    public static void init() {
        GTOres.create(SkufAddon.id("skufit_vein"), vein -> vein
                .clusterSize(UniformInt.of(24, 40))
                .density(0.35f)
                .weight(70)
                .layer(WorldGenLayers.STONE)
                .heightRangeUniform(16, 90)
                .biomes(BiomeTags.IS_OVERWORLD)
                .cuboidVeinGenerator(generator -> generator
                        .top(b -> b.mat(SkufMaterials.skufit).size(2))
                        .middle(b -> b.mat(SkufMaterials.skufit).size(3))
                        .bottom(b -> b.mat(SkufMaterials.skufit).size(2))
                        .spread(b -> b.mat(SkufMaterials.skufit))));

        GTOres.create(SkufAddon.id("pokhuit_vein"), vein -> vein
                .clusterSize(UniformInt.of(20, 32))
                .density(0.28f)
                .weight(45)
                .layer(WorldGenLayers.DEEPSLATE)
                .heightRangeUniform(-50, 24)
                .biomes(BiomeTags.IS_OVERWORLD)
                .cuboidVeinGenerator(generator -> generator
                        .top(b -> b.mat(SkufMaterials.pokhuit).size(2))
                        .middle(b -> b.mat(SkufMaterials.pokhuit).size(3))
                        .bottom(b -> b.mat(SkufMaterials.pokhuit).size(2))
                        .spread(b -> b.mat(SkufMaterials.pokhuit))));

        GTOres.create(SkufAddon.id("chelyabinsk_shale_vein"), vein -> vein
                .clusterSize(UniformInt.of(16, 28))
                .density(0.2f)
                .weight(25)
                .layer(WorldGenLayers.DEEPSLATE)
                .heightRangeUniform(-58, 8)
                .biomes(BiomeTags.IS_OVERWORLD)
                .cuboidVeinGenerator(generator -> generator
                        .top(b -> b.mat(SkufMaterials.chelyabinskShale).size(2))
                        .middle(b -> b.mat(SkufMaterials.chelyabinskShale).size(3))
                        .bottom(b -> b.mat(SkufMaterials.chelyabinskShale).size(2))
                        .spread(b -> b.mat(SkufMaterials.chelyabinskShale))));
    }
}
