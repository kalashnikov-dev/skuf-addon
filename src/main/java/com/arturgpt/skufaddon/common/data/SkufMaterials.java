package com.arturgpt.skufaddon.common.data;

import com.arturgpt.skufaddon.SkufAddon;

import com.gregtechceu.gtceu.api.GTValues;
import com.gregtechceu.gtceu.api.data.chemical.material.Material;
import com.gregtechceu.gtceu.api.data.chemical.material.info.MaterialIconSet;
import com.gregtechceu.gtceu.api.fluids.FluidBuilder;
import com.gregtechceu.gtceu.api.fluids.attribute.FluidAttributes;

import static com.gregtechceu.gtceu.api.data.chemical.material.info.MaterialFlags.*;

public class SkufMaterials {

    public static Material skufit;
    public static Material pokhuit;
    public static Material sweat;
    public static Material puffSmoke;
    public static Material jizhnyak;

    public static Material normieDust;
    public static Material honestSteel;
    public static Material correctMatter;
    public static Material uralIsotope;
    public static Material stabilizedVibe;
    public static Material chelyabinskShale;

    public static Material slagIgnore;
    public static Material zhizhnyakLoss;
    public static Material ugarGas;
    public static Material hiddenSweat;
    public static Material condensedSweat;
    public static Material dilutedSweat;

    public static Material crystallizedDodikSweat;

    public static Material technicalTears;
    public static Material coolantOfDenial;
    public static Material warmVibeSteam;

    public static Material padikNobleGas;
    public static Material denseJizhnyak;

    public static Material brokenMonitor;

    public static void init() {
        skufit = new Material.Builder(SkufAddon.id("skufit"))
                .ingot()
                .ore()
                .liquid(new FluidBuilder().temperature(1200))
                .color(0x7A5C3A)
                .iconSet(MaterialIconSet.DULL)
                .flags(
                        GENERATE_PLATE,
                        GENERATE_ROD,
                        GENERATE_GEAR,
                        GENERATE_BOLT_SCREW,
                        GENERATE_FOIL,
                        GENERATE_FRAME)
                .buildAndRegister();

        pokhuit = new Material.Builder(SkufAddon.id("pokhuit"))
                .ingot()
                .ore()
                .liquid(new FluidBuilder().temperature(2400))
                .color(0x3A7A5C)
                .iconSet(MaterialIconSet.SHINY)
                .cableProperties(GTValues.V[GTValues.MV], 4, 4, false)
                .flags(
                        GENERATE_PLATE,
                        GENERATE_ROD,
                        GENERATE_GEAR,
                        GENERATE_BOLT_SCREW,
                        GENERATE_FOIL,
                        GENERATE_FRAME)
                .buildAndRegister();

        sweat = new Material.Builder(SkufAddon.id("sweat"))
                .liquid(new FluidBuilder()
                        .temperature(310)
                        .attribute(FluidAttributes.ACID))
                .color(0xD4C84A)
                .buildAndRegister();

        puffSmoke = new Material.Builder(SkufAddon.id("puff_smoke"))
                .gas(new FluidBuilder()
                        .temperature(600))
                .color(0x2A2A2A)
                .buildAndRegister();

        jizhnyak = new Material.Builder(SkufAddon.id("jizhnyak"))
                .liquid(new FluidBuilder()
                        .temperature(340)
                        .attribute(FluidAttributes.ACID))
                .color(0x5F5E41)
                .buildAndRegister();

        normieDust = new Material.Builder(SkufAddon.id("normie_dust"))
                .dust()
                .color(0x8A8A8A)
                .iconSet(MaterialIconSet.ROUGH)
                .buildAndRegister();

        honestSteel = new Material.Builder(SkufAddon.id("honest_steel"))
                .ingot()
                .liquid(new FluidBuilder().temperature(1700))
                .color(0x9AA4AD)
                .iconSet(MaterialIconSet.METALLIC)
                .cableProperties(GTValues.V[GTValues.LV], 2, 2, false)
                .flags(
                        GENERATE_PLATE,
                        GENERATE_ROD,
                        GENERATE_FOIL)
                .buildAndRegister();

        correctMatter = new Material.Builder(SkufAddon.id("correct_matter"))
                .gem()
                .color(0x36C9B0)
                .iconSet(MaterialIconSet.GEM_VERTICAL)
                .flags(GENERATE_PLATE)
                .buildAndRegister();

        uralIsotope = new Material.Builder(SkufAddon.id("ural_isotope"))
                .dust()
                .color(0x66FF33)
                .iconSet(MaterialIconSet.RADIOACTIVE)
                .radioactiveHazard(2.0f)
                .buildAndRegister();

        stabilizedVibe = new Material.Builder(SkufAddon.id("stabilized_vibe"))
                .liquid(new FluidBuilder()
                        .temperature(295))
                .color(0x49E0D0)
                .iconSet(MaterialIconSet.SHINY)
                .buildAndRegister();

        chelyabinskShale = new Material.Builder(SkufAddon.id("chelyabinsk_shale"))
                .dust()
                .ore()
                .color(0x4C7A2E)
                .iconSet(MaterialIconSet.ROUGH)
                .radioactiveHazard(1.0f)
                .addOreByproducts(uralIsotope)
                .buildAndRegister();

        slagIgnore = new Material.Builder(SkufAddon.id("slag_ignore"))
                .dust()
                .color(0x4A4038)
                .iconSet(MaterialIconSet.ROUGH)
                .buildAndRegister();

        zhizhnyakLoss = new Material.Builder(SkufAddon.id("zhizhnyak_loss"))
                .liquid(new FluidBuilder().temperature(330))
                .color(0x3E3A2A)
                .buildAndRegister();

        ugarGas = new Material.Builder(SkufAddon.id("ugar_gas"))
                .gas(new FluidBuilder().temperature(720))
                .color(0xB85C1E)
                .buildAndRegister();

        hiddenSweat = new Material.Builder(SkufAddon.id("hidden_sweat"))
                .liquid(new FluidBuilder()
                        .temperature(360)
                        .attribute(FluidAttributes.ACID))
                .color(0xC0A83A)
                .buildAndRegister();

        condensedSweat = new Material.Builder(SkufAddon.id("condensed_sweat"))
                .liquid(new FluidBuilder().temperature(305))
                .color(0xE6D24A)
                .iconSet(MaterialIconSet.SHINY)
                .buildAndRegister();

        dilutedSweat = new Material.Builder(SkufAddon.id("diluted_sweat"))
                .liquid(new FluidBuilder()
                        .temperature(300)
                        .color(0xA8E0D880))
                .color(0xE0D880)
                .buildAndRegister();

        technicalTears = new Material.Builder(SkufAddon.id("technical_tears"))
                .dust()
                .liquid(new FluidBuilder().temperature(285))
                .color(0x4F7FB5)
                .iconSet(MaterialIconSet.SHINY)
                .buildAndRegister();

        coolantOfDenial = new Material.Builder(SkufAddon.id("coolant_of_denial"))
                .liquid(new FluidBuilder().temperature(255))
                .color(0x2FB7C9)
                .iconSet(MaterialIconSet.SHINY)
                .buildAndRegister();

        warmVibeSteam = new Material.Builder(SkufAddon.id("warm_vibe_steam"))
                .gas(new FluidBuilder().temperature(380))
                .color(0xC9B98F)
                .buildAndRegister();

        crystallizedDodikSweat = new Material.Builder(SkufAddon.id("crystallized_dodik_sweat"))
                .gem()
                .color(0xE6C84A)
                .iconSet(MaterialIconSet.SHINY)
                .flags(GENERATE_PLATE)
                .cableProperties(GTValues.V[GTValues.HV], 4, 2)
                .buildAndRegister();

        padikNobleGas = new Material.Builder(SkufAddon.id("padik_noble_gas"))
                .gas(new FluidBuilder().temperature(120))
                .color(0x6B5E8C)
                .iconSet(MaterialIconSet.SHINY)
                .buildAndRegister();

        denseJizhnyak = new Material.Builder(SkufAddon.id("dense_jizhnyak"))
                .liquid(new FluidBuilder().temperature(330))
                .color(0x3E5A2A)
                .buildAndRegister();

        brokenMonitor = new Material.Builder(SkufAddon.id("broken_monitor"))
                .gem()
                .color(0x2A2A4A)
                .iconSet(MaterialIconSet.SHINY)
                .buildAndRegister();
    }
}
