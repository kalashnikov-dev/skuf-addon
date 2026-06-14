package com.arturgpt.skufaddon;

import com.gregtechceu.gtceu.api.data.chemical.material.Material;
import com.gregtechceu.gtceu.api.data.chemical.material.info.MaterialIconSet;
import com.gregtechceu.gtceu.api.fluids.FluidBuilder;
import com.gregtechceu.gtceu.api.fluids.attribute.FluidAttributes;

import net.minecraft.resources.ResourceLocation;

import static com.gregtechceu.gtceu.api.data.chemical.material.info.MaterialFlags.*;

public class SkufMaterials {

    public static Material skufit;
    public static Material pokhuit;

    public static Material sweat;
    public static Material puffSmoke;

    public static Material jizhnyak;

    public static void init() {
        skufit = new Material.Builder(ResourceLocation.fromNamespaceAndPath(SkufAddon.MOD_ID, "skufit"))
                .ingot()
                .liquid(new FluidBuilder().temperature(1200))
                .color(0x7A5C3A)
                .iconSet(MaterialIconSet.DULL)
                .flags(
                        GENERATE_PLATE,
                        GENERATE_ROD,
                        GENERATE_GEAR,
                        GENERATE_BOLT_SCREW,
                        GENERATE_FOIL)
                .buildAndRegister();

        pokhuit = new Material.Builder(ResourceLocation.fromNamespaceAndPath(SkufAddon.MOD_ID, "pokhuit"))
                .ingot()
                .liquid(new FluidBuilder().temperature(2400))
                .color(0x3A7A5C)
                .iconSet(MaterialIconSet.SHINY)
                .flags(
                        GENERATE_PLATE,
                        GENERATE_ROD,
                        GENERATE_GEAR,
                        GENERATE_BOLT_SCREW,
                        GENERATE_FOIL)
                .buildAndRegister();

        sweat = new Material.Builder(ResourceLocation.fromNamespaceAndPath(SkufAddon.MOD_ID, "sweat"))
                .liquid(new FluidBuilder()
                        .temperature(310)
                        .attribute(FluidAttributes.ACID))
                .color(0xD4C84A)
                .buildAndRegister();

        puffSmoke = new Material.Builder(ResourceLocation.fromNamespaceAndPath(SkufAddon.MOD_ID, "puff_smoke"))
                .gas(new FluidBuilder()
                        .temperature(600))
                .color(0x2A2A2A)
                .buildAndRegister();

        jizhnyak = new Material.Builder(ResourceLocation.fromNamespaceAndPath(SkufAddon.MOD_ID, "jizhnyak"))
                .liquid(new FluidBuilder()
                        .temperature(340)
                        .attribute(FluidAttributes.ACID))
                .color(0x5F5E41)
                .buildAndRegister();
    }
}
