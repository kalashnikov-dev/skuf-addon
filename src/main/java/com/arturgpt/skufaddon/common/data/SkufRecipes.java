package com.arturgpt.skufaddon.common.data;

import com.arturgpt.skufaddon.common.machine.multiblock.sauna.SaunaEgoraMachine;

import com.gregtechceu.gtceu.api.GTValues;
import com.gregtechceu.gtceu.api.data.chemical.ChemicalHelper;
import com.gregtechceu.gtceu.common.data.GTMaterials;
import com.gregtechceu.gtceu.common.data.GTRecipeTypes;
import com.gregtechceu.gtceu.data.recipe.VanillaRecipeHelper;

import net.minecraft.data.recipes.FinishedRecipe;
import net.minecraft.world.item.Items;

import java.util.function.Consumer;

import static com.gregtechceu.gtceu.api.data.tag.TagPrefix.*;

public class SkufRecipes {

    public static void init(Consumer<FinishedRecipe> provider) {
        baseRecipes(provider);
        vanillaCrafting(provider);
        bootstrapFix(provider);
        circuitsChain(provider);
        machineCrafting(provider);
        productionChain(provider);
        stabilizerChain(provider);
        recyclingChain(provider);
        myposhkoChain(provider);
        saunaChain(provider);
        gameplayBreakdownChain(provider);
        endgameChain(provider);
        mvpOrphanFixes(provider);
        exampleRecipes(provider);
    }

    private static void baseRecipes(Consumer<FinishedRecipe> provider) {
        SkufRecipeTypes.NORMIS_FILTRATION_RECIPES.recipeBuilder("normis_filtration")
                .inputFluids(GTMaterials.Water.getFluid(1000))
                .outputFluids(SkufMaterials.sweat.getFluid(200))
                .duration(600)
                .EUt(30)
                .save(provider);
    }

    private static void bootstrapFix(Consumer<FinishedRecipe> provider) {
        GTRecipeTypes.CENTRIFUGE_RECIPES.recipeBuilder("puff_smoke_extraction")
                .inputItems(dust, SkufMaterials.normieDust)
                .circuitMeta(5)
                .outputFluids(SkufMaterials.puffSmoke.getFluid(250))
                .duration(160)
                .EUt(16)
                .save(provider);
    }

    // SKU-47: 3 tiered circuit boards — Dodik → Lyudskaya → Zapizdosh
    private static void circuitsChain(Consumer<FinishedRecipe> provider) {
        // LV: dodik_circuit_basic from 2x honestSteelPlate + 2x electrically_wet_sweat + circuit(1)
        GTRecipeTypes.CHEMICAL_RECIPES.recipeBuilder("craft_dodik_board")
                .inputItems(plate, SkufMaterials.honestSteel, 2)
                .inputFluids(SkufMaterials.sweat.getFluid(200))
                .circuitMeta(1)
                .outputItems(SkufItems.DODIK_CIRCUIT_BASIC)
                .duration(200)
                .EUt(GTValues.V[GTValues.LV])
                .save(provider);

        // MV: dodik_circuit_advanced from 2x dodik_circuit_basic + 2x pokhuitPlate + circuit(2)
        GTRecipeTypes.CHEMICAL_RECIPES.recipeBuilder("craft_lyudskaya_board")
                .inputItems(SkufItems.DODIK_CIRCUIT_BASIC, 2)
                .inputItems(plate, SkufMaterials.pokhuit, 2)
                .circuitMeta(2)
                .outputItems(SkufItems.DODIK_CIRCUIT_ADVANCED)
                .duration(240)
                .EUt(GTValues.V[GTValues.MV])
                .save(provider);

        // HV: dodik_circuit_extreme from 2x dodik_circuit_advanced + 2x crystallizedDodikSweatPlate + circuit(3)
        GTRecipeTypes.CHEMICAL_RECIPES.recipeBuilder("craft_zapizdosh_mainframe")
                .inputItems(SkufItems.DODIK_CIRCUIT_ADVANCED, 2)
                .inputItems(plate, SkufMaterials.crystallizedDodikSweat, 2)
                .circuitMeta(3)
                .outputItems(SkufItems.DODIK_CIRCUIT_EXTREME)
                .duration(300)
                .EUt(GTValues.V[GTValues.HV])
                .save(provider);
    }

    private static void machineCrafting(Consumer<FinishedRecipe> provider) {
        // ── LV: dodik_circuit_basic + honestSteel cable ─────────────────────────
        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_normis_filtration_machine")
                .inputItems(SkufComponentMachines.SMOLDERING_PUKAN[GTValues.LV].asStack())
                .inputItems(dust, SkufMaterials.normieDust, 2)
                .inputItems(SkufItems.DODIK_CIRCUIT_BASIC)
                .inputItems(cableGtSingle, SkufMaterials.honestSteel)
                .outputItems(SkufSingleblockMachines.NORMIS_FILTRATION_MACHINE[GTValues.LV].asStack())
                .duration(200)
                .EUt(30)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_cnc_machine")
                .inputItems(SkufComponentMachines.SMOLDERING_PUKAN[GTValues.LV].asStack())
                .inputItems(SkufItems.CNC_BIT, 2)
                .inputItems(SkufItems.DODIK_CIRCUIT_BASIC)
                .inputItems(cableGtSingle, SkufMaterials.honestSteel)
                .outputItems(SkufSingleblockMachines.CNC_MACHINE[GTValues.LV].asStack())
                .duration(200)
                .EUt(30)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_pot_distillery")
                .inputItems(SkufComponentMachines.SMOLDERING_PUKAN[GTValues.LV].asStack())
                .inputItems(frameGt, SkufMaterials.skufit)
                .inputItems(SkufItems.DODIK_CIRCUIT_BASIC)
                .inputItems(cableGtSingle, SkufMaterials.honestSteel)
                .outputItems(SkufSingleblockMachines.POT_DISTILLERY[GTValues.LV].asStack())
                .duration(200)
                .EUt(30)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_vibe_stabilizer")
                .inputItems(SkufComponentMachines.SMOLDERING_PUKAN[GTValues.LV].asStack())
                .inputItems(plate, SkufMaterials.correctMatter)
                .inputItems(frameGt, SkufMaterials.pokhuit)
                .inputItems(SkufItems.DODIK_CIRCUIT_BASIC)
                .inputItems(cableGtSingle, SkufMaterials.honestSteel)
                .outputItems(SkufSingleblockMachines.VIBE_STABILIZER[GTValues.LV].asStack())
                .duration(300)
                .EUt(60)
                .save(provider);

        // ── MV: dodik_circuit_advanced + pokhuit cable ────────────────────────
        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_normis_filtration_machine_mv")
                .inputItems(SkufComponentMachines.SMOLDERING_PUKAN[GTValues.MV].asStack())
                .inputItems(dust, SkufMaterials.normieDust, 2)
                .inputItems(SkufItems.DODIK_CIRCUIT_ADVANCED)
                .inputItems(cableGtSingle, SkufMaterials.pokhuit)
                .outputItems(SkufSingleblockMachines.NORMIS_FILTRATION_MACHINE[GTValues.MV].asStack())
                .duration(200)
                .EUt(120)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_cnc_machine_mv")
                .inputItems(SkufComponentMachines.SMOLDERING_PUKAN[GTValues.MV].asStack())
                .inputItems(SkufItems.CNC_BIT, 2)
                .inputItems(SkufItems.DODIK_CIRCUIT_ADVANCED)
                .inputItems(cableGtSingle, SkufMaterials.pokhuit)
                .outputItems(SkufSingleblockMachines.CNC_MACHINE[GTValues.MV].asStack())
                .duration(200)
                .EUt(120)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_pot_distillery_mv")
                .inputItems(SkufComponentMachines.SMOLDERING_PUKAN[GTValues.MV].asStack())
                .inputItems(frameGt, SkufMaterials.skufit)
                .inputItems(SkufItems.DODIK_CIRCUIT_ADVANCED)
                .inputItems(cableGtSingle, SkufMaterials.pokhuit)
                .outputItems(SkufSingleblockMachines.POT_DISTILLERY[GTValues.MV].asStack())
                .duration(200)
                .EUt(120)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_vibe_stabilizer_mv")
                .inputItems(SkufComponentMachines.SMOLDERING_PUKAN[GTValues.MV].asStack())
                .inputItems(plate, SkufMaterials.correctMatter)
                .inputItems(frameGt, SkufMaterials.pokhuit)
                .inputItems(SkufItems.DODIK_CIRCUIT_ADVANCED)
                .inputItems(cableGtSingle, SkufMaterials.pokhuit)
                .outputItems(SkufSingleblockMachines.VIBE_STABILIZER[GTValues.MV].asStack())
                .duration(300)
                .EUt(240)
                .save(provider);

        // ── HV: dodik_circuit_extreme + crystallizedDodikSweat cable ──────────
        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_normis_filtration_machine_hv")
                .inputItems(SkufComponentMachines.SMOLDERING_PUKAN[GTValues.HV].asStack())
                .inputItems(dust, SkufMaterials.normieDust, 2)
                .inputItems(SkufItems.DODIK_CIRCUIT_EXTREME)
                .inputItems(cableGtSingle, SkufMaterials.crystallizedDodikSweat)
                .outputItems(SkufSingleblockMachines.NORMIS_FILTRATION_MACHINE[GTValues.HV].asStack())
                .duration(200)
                .EUt(480)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_cnc_machine_hv")
                .inputItems(SkufComponentMachines.SMOLDERING_PUKAN[GTValues.HV].asStack())
                .inputItems(SkufItems.CNC_BIT, 2)
                .inputItems(SkufItems.DODIK_CIRCUIT_EXTREME)
                .inputItems(cableGtSingle, SkufMaterials.crystallizedDodikSweat)
                .outputItems(SkufSingleblockMachines.CNC_MACHINE[GTValues.HV].asStack())
                .duration(200)
                .EUt(480)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_pot_distillery_hv")
                .inputItems(SkufComponentMachines.SMOLDERING_PUKAN[GTValues.HV].asStack())
                .inputItems(frameGt, SkufMaterials.skufit)
                .inputItems(SkufItems.DODIK_CIRCUIT_EXTREME)
                .inputItems(cableGtSingle, SkufMaterials.crystallizedDodikSweat)
                .outputItems(SkufSingleblockMachines.POT_DISTILLERY[GTValues.HV].asStack())
                .duration(200)
                .EUt(480)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_vibe_stabilizer_hv")
                .inputItems(SkufComponentMachines.SMOLDERING_PUKAN[GTValues.HV].asStack())
                .inputItems(plate, SkufMaterials.correctMatter)
                .inputItems(frameGt, SkufMaterials.pokhuit)
                .inputItems(SkufItems.DODIK_CIRCUIT_EXTREME)
                .inputItems(cableGtSingle, SkufMaterials.crystallizedDodikSweat)
                .outputItems(SkufSingleblockMachines.VIBE_STABILIZER[GTValues.HV].asStack())
                .duration(300)
                .EUt(960)
                .save(provider);
    }

    private static void productionChain(Consumer<FinishedRecipe> provider) {
        SkufRecipeTypes.NORMIS_FILTRATION_RECIPES.recipeBuilder("normie_dust_from_trash")
                .inputItems(Items.ROTTEN_FLESH)
                .outputItems(dust, SkufMaterials.normieDust)
                .outputFluids(SkufMaterials.sweat.getFluid(100))
                .duration(160)
                .EUt(16)
                .save(provider);

        GTRecipeTypes.ALLOY_SMELTER_RECIPES.recipeBuilder("honest_steel_alloy")
                .inputItems(ingot, SkufMaterials.skufit)
                .inputItems(dust, SkufMaterials.normieDust, 2)
                .outputItems(ingot, SkufMaterials.honestSteel, 2)
                .duration(240)
                .EUt(30)
                .save(provider);

        GTRecipeTypes.MIXER_RECIPES.recipeBuilder("jizhnyak_from_normie")
                .inputItems(dust, SkufMaterials.normieDust)
                .inputFluids(SkufMaterials.sweat.getFluid(1000))
                .inputFluids(SkufMaterials.puffSmoke.getFluid(1000))
                .outputFluids(SkufMaterials.jizhnyak.getFluid(2000))
                .duration(180)
                .EUt(30)
                .save(provider);

        SkufRecipeTypes.POT_DISTILLERY_RECIPES.recipeBuilder("jizhnyak_distillation")
                .inputFluids(SkufMaterials.jizhnyak.getFluid(1000))
                .outputItems(dust, SkufMaterials.correctMatter)
                .outputFluids(SkufMaterials.puffSmoke.getFluid(500))
                .duration(260)
                .EUt(48)
                .save(provider);

        GTRecipeTypes.AUTOCLAVE_RECIPES.recipeBuilder("correct_matter_crystallization")
                .inputItems(dust, SkufMaterials.correctMatter)
                .inputFluids(GTMaterials.Water.getFluid(250))
                .outputItems(gem, SkufMaterials.correctMatter)
                .duration(400)
                .EUt(60)
                .save(provider);

        GTRecipeTypes.CENTRIFUGE_RECIPES.recipeBuilder("ural_isotope_extraction")
                .inputFluids(SkufMaterials.jizhnyak.getFluid(1000))
                .circuitMeta(2)
                .outputItems(dust, SkufMaterials.uralIsotope)
                .outputFluids(SkufMaterials.sweat.getFluid(500))
                .duration(500)
                .EUt(60)
                .save(provider);

        SkufRecipeTypes.CNC_RECIPES.recipeBuilder("cnc_bit_from_rod")
                .inputItems(rod, SkufMaterials.honestSteel)
                .circuitMeta(1)
                .outputItems(SkufItems.CNC_BIT, 2)
                .duration(120)
                .EUt(16)
                .save(provider);

        SkufRecipeTypes.CNC_RECIPES.recipeBuilder("cnc_cutter_assembly")
                .inputItems(SkufItems.CNC_BIT, 2)
                .inputItems(plate, SkufMaterials.honestSteel)
                .circuitMeta(2)
                .outputItems(SkufItems.CNC_CUTTER)
                .duration(200)
                .EUt(30)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("pravilnaya_vesh_assembly")
                .inputItems(gem, SkufMaterials.correctMatter, 2)
                .inputItems(plate, SkufMaterials.honestSteel, 2)
                .inputItems(SkufItems.CNC_CUTTER)
                .inputFluids(SkufMaterials.stabilizedVibe.getFluid(250))
                .inputItems(SkufItems.DODIK_CIRCUIT_ADVANCED)
                .outputItems(SkufItems.PRAVILNAYA_VESH)
                .duration(600)
                .EUt(120)
                .save(provider);
    }

    private static void stabilizerChain(Consumer<FinishedRecipe> provider) {
        SkufRecipeTypes.VIBE_STABILIZER_RECIPES.recipeBuilder("stabilized_vibe_synthesis")
                .inputItems(dust, SkufMaterials.correctMatter)
                .inputFluids(SkufMaterials.sweat.getFluid(1000))
                .outputFluids(SkufMaterials.stabilizedVibe.getFluid(1000))
                .duration(240)
                .EUt(48)
                .save(provider);

        GTRecipeTypes.AUTOCLAVE_RECIPES.recipeBuilder("vibe_infused_crystallization")
                .inputItems(dust, SkufMaterials.correctMatter, 2)
                .inputFluids(SkufMaterials.stabilizedVibe.getFluid(500))
                .outputItems(gem, SkufMaterials.correctMatter, 3)
                .duration(300)
                .EUt(60)
                .save(provider);
    }

    private static void recyclingChain(Consumer<FinishedRecipe> provider) {
        GTRecipeTypes.CENTRIFUGE_RECIPES.recipeBuilder("reclaim_zhizhnyak_loss")
                .inputFluids(SkufMaterials.zhizhnyakLoss.getFluid(1000))
                .circuitMeta(4)
                .outputFluids(SkufMaterials.sweat.getFluid(400))
                .outputItems(dust, SkufMaterials.normieDust)
                .duration(220)
                .EUt(60)
                .save(provider);

        GTRecipeTypes.ARC_FURNACE_RECIPES.recipeBuilder("repair_melted_capacitor")
                .inputItems(SkufItems.MELTED_CAPACITOR.asStack(2))
                .inputFluids(SkufMaterials.condensedSweat.getFluid(250))
                .outputItems(ingot, SkufMaterials.honestSteel)
                .duration(200)
                .EUt(90)
                .save(provider);

        GTRecipeTypes.MACERATOR_RECIPES.recipeBuilder("repair_burnt_cable_debris")
                .inputItems(SkufItems.BURNT_CABLE_DEBRIS.asStack(3))
                .outputItems(dust, SkufMaterials.normieDust, 2)
                .outputFluids(SkufMaterials.ugarGas.getFluid(500))
                .duration(180)
                .EUt(48)
                .save(provider);
    }

    private static void myposhkoChain(Consumer<FinishedRecipe> provider) {
        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_myposhko_script")
                .inputItems(dust, SkufMaterials.normieDust, 2)
                .inputItems(gem, SkufMaterials.correctMatter)
                .inputFluids(SkufMaterials.stabilizedVibe.getFluid(250))
                .inputItems(SkufItems.DODIK_CIRCUIT_ADVANCED)
                .outputItems(SkufItems.MYPOSHKO_SCRIPT)
                .duration(160)
                .EUt(48)
                .save(provider);

        GTRecipeTypes.CHEMICAL_RECIPES.recipeBuilder("comfort_technical_tears")
                .inputItems(dust, SkufMaterials.technicalTears, 2)
                .inputFluids(SkufMaterials.stabilizedVibe.getFluid(500))
                .outputItems(dust, SkufMaterials.normieDust)
                .outputFluids(SkufMaterials.puffSmoke.getFluid(250))
                .duration(220)
                .EUt(120)
                .save(provider);
    }

    private static void saunaChain(Consumer<FinishedRecipe> provider) {
        // EMI/JEI info recipe — base rate at EV with no Tilt machines inside; see recipe type tooltips.
        SkufRecipeTypes.SAUNA_EGORA_RECIPES.recipeBuilder("warm_vibe_steam")
                .inputFluids(GTMaterials.Water.getFluid(SaunaEgoraMachine.STEAM_BASE_MB))
                .outputFluids(SkufMaterials.warmVibeSteam.getFluid(SaunaEgoraMachine.STEAM_BASE_MB))
                .duration(20)
                .EUt(GTValues.VA[GTValues.EV])
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_egor_core")
                .inputItems(gem, SkufMaterials.correctMatter, 2)
                .inputItems(plate, SkufMaterials.honestSteel, 4)
                .inputFluids(SkufMaterials.stabilizedVibe.getFluid(1000))
                .circuitMeta(8)
                .outputItems(SkufItems.EGOR_CORE)
                .duration(400)
                .EUt(1920)
                .save(provider);

        GTRecipeTypes.CENTRIFUGE_RECIPES.recipeBuilder("condense_warm_vibe_steam")
                .inputFluids(SkufMaterials.warmVibeSteam.getFluid(1500))
                .outputFluids(GTMaterials.Water.getFluid(1000))
                .outputFluids(SkufMaterials.ugarGas.getFluid(250))
                .duration(100)
                .EUt(GTValues.VA[GTValues.EV])
                .save(provider);

        GTRecipeTypes.CHEMICAL_RECIPES.recipeBuilder("brew_coolant_of_denial")
                .inputItems(dust, SkufMaterials.technicalTears, 2)
                .inputItems(dust, SkufMaterials.pokhuit, 1)
                .inputFluids(GTMaterials.Water.getFluid(1000))
                .outputFluids(SkufMaterials.coolantOfDenial.getFluid(1000))
                .duration(160)
                .EUt(480)
                .save(provider);
    }

    private static void gameplayBreakdownChain(Consumer<FinishedRecipe> provider) {
        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_broken_monitor_block")
                .inputItems(SkufItems.MELTED_CAPACITOR, 1)
                .inputItems(dust, SkufMaterials.normieDust, 2)
                .inputItems(plate, SkufMaterials.honestSteel, 1)
                .inputItems(gem, SkufMaterials.correctMatter)
                .circuitMeta(7)
                .outputItems(block, SkufMaterials.brokenMonitor)
                .duration(300)
                .EUt(GTValues.V[GTValues.MV])
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_raw_demo")
                .inputItems(SkufItems.CHARRED_DEVELOPER_CIRCUIT)
                .inputItems(SkufItems.MYPOSHKO_SCRIPT)
                .inputItems(dust, SkufMaterials.normieDust, 2)
                .inputFluids(SkufMaterials.stabilizedVibe.getFluid(250))
                .circuitMeta(9)
                .outputItems(SkufItems.RAW_DEMO)
                .duration(160)
                .EUt(GTValues.V[GTValues.MV])
                .save(provider);

        SkufRecipeTypes.RAZBOR_GEYMPLAYA_RECIPES.recipeBuilder("demo_to_technical_tears")
                .inputItems(SkufItems.RAW_DEMO)
                .outputFluids(SkufMaterials.technicalTears.getFluid(500))
                .duration(240)
                .EUt(GTValues.V[GTValues.MV])
                .save(provider);

        GTRecipeTypes.CENTRIFUGE_RECIPES.recipeBuilder("dry_technical_tears")
                .inputFluids(SkufMaterials.technicalTears.getFluid(500))
                .outputItems(dust, SkufMaterials.technicalTears)
                .outputFluids(GTMaterials.Water.getFluid(250))
                .duration(160)
                .EUt(GTValues.V[GTValues.MV])
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_razbor_geympleya")
                .inputItems(frameGt, SkufMaterials.pokhuit, 20)
                .inputItems(block, SkufMaterials.brokenMonitor, 12)
                .inputItems(SkufItems.DODIK_CIRCUIT_ADVANCED)
                .inputItems(SkufComponentMachines.SMOLDERING_PUKAN[GTValues.MV].asStack())
                .circuitMeta(12)
                .outputItems(SkufMultiblockMachines.RAZBOR_GEYMPLAYA.asStack())
                .duration(600)
                .EUt(GTValues.V[GTValues.MV])
                .save(provider);
    }

    private static void endgameChain(Consumer<FinishedRecipe> provider) {
        GTRecipeTypes.CENTRIFUGE_RECIPES.recipeBuilder("condense_dense_jizhnyak")
                .inputFluids(SkufMaterials.jizhnyak.getFluid(2000))
                .circuitMeta(3)
                .outputFluids(SkufMaterials.denseJizhnyak.getFluid(1000))
                .outputFluids(SkufMaterials.zhizhnyakLoss.getFluid(500))
                .duration(160)
                .EUt(120)
                .save(provider);

        GTRecipeTypes.CHEMICAL_RECIPES.recipeBuilder("synthesize_padik_noble_gas")
                .inputFluids(SkufMaterials.denseJizhnyak.getFluid(1000))
                .inputFluids(SkufMaterials.stabilizedVibe.getFluid(200))
                .outputFluids(SkufMaterials.padikNobleGas.getFluid(500))
                .outputItems(dust, SkufMaterials.normieDust, 1)
                .duration(200)
                .EUt(1920)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("compress_normis_singularity")
                .inputItems(dust, SkufMaterials.normieDust, 16)
                .inputItems(dust, SkufMaterials.slagIgnore, 4)
                .circuitMeta(16)
                .outputItems(SkufItems.NORMIS_SINGULARITY)
                .duration(400)
                .EUt(1920)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_antizoomer_core")
                .inputItems(gem, SkufMaterials.correctMatter, 2)
                .inputItems(plate, SkufMaterials.honestSteel, 2)
                .inputItems(dust, SkufMaterials.uralIsotope, 4)
                .circuitMeta(10)
                .outputItems(SkufItems.ANTIZOOMER_CORE)
                .duration(300)
                .EUt(2048)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_correct_developer_schematic")
                .inputItems(SkufItems.CHARRED_DEVELOPER_CIRCUIT)
                .inputItems(gem, SkufMaterials.correctMatter, 1)
                .inputFluids(SkufMaterials.stabilizedVibe.getFluid(500))
                .circuitMeta(11)
                .outputItems(SkufItems.CORRECT_DEVELOPER_SCHEMATIC)
                .duration(300)
                .EUt(2048)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_absolute_pohuit")
                .inputItems(SkufItems.PRAVILNAYA_VESH)
                .inputItems(dust, SkufMaterials.uralIsotope, 2)
                .inputItems(SkufItems.ANTIZOOMER_CORE)
                .inputItems(SkufItems.CORRECT_DEVELOPER_SCHEMATIC)
                .inputFluids(SkufMaterials.stabilizedVibe.getFluid(1000))
                .circuitMeta(12)
                .outputItems(SkufItems.ABSOLUTE_POHUIT)
                .duration(600)
                .EUt(8192)
                .save(provider);

        GTRecipeTypes.CHEMICAL_RECIPES.recipeBuilder("craft_correct_matter_microcapsule")
                .inputItems(gem, SkufMaterials.correctMatter, 1)
                .inputFluids(SkufMaterials.denseJizhnyak.getFluid(500))
                .inputFluids(SkufMaterials.padikNobleGas.getFluid(250))
                .outputItems(SkufItems.CORRECT_MATTER_MICROCAPSULE)
                .duration(200)
                .EUt(1920)
                .save(provider);

        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("craft_arturian_mainframe")
                .inputItems(plate, SkufMaterials.honestSteel, 8)
                .inputItems(gem, SkufMaterials.correctMatter, 4)
                .inputItems(SkufItems.MYPOSHKO_SCRIPT)
                .inputFluids(SkufMaterials.stabilizedVibe.getFluid(2000))
                .circuitMeta(14)
                .outputItems(SkufItems.ARTURIAN_MAINFRAME)
                .duration(800)
                .EUt(8192)
                .save(provider);
    }

    private static void mvpOrphanFixes(Consumer<FinishedRecipe> provider) {
        // condensed_sweat source: concentrate raw sweat (also feeds repair_melted_capacitor)
        GTRecipeTypes.CENTRIFUGE_RECIPES.recipeBuilder("condense_sweat")
                .inputFluids(SkufMaterials.sweat.getFluid(1000))
                .circuitMeta(1)
                .outputFluids(SkufMaterials.condensedSweat.getFluid(250))
                .outputFluids(GTMaterials.Water.getFluid(750))
                .duration(120)
                .EUt(24)
                .save(provider);

        // crystallized_dodik_sweat (HV conductor) source: crystallize condensed sweat
        // around a correct_matter seed. Gates the HV cable behind MV chemistry.
        GTRecipeTypes.CHEMICAL_RECIPES.recipeBuilder("crystallize_dodik_sweat")
                .inputItems(dust, SkufMaterials.correctMatter)
                .inputFluids(SkufMaterials.condensedSweat.getFluid(1000))
                .circuitMeta(2)
                .outputItems(dust, SkufMaterials.crystallizedDodikSweat, 2)
                .duration(200)
                .EUt(GTValues.V[GTValues.MV])
                .save(provider);

        // ugar gas scrubber: ugar gas + water -> diluted sweat (EV+)
        GTRecipeTypes.CHEMICAL_RECIPES.recipeBuilder("ugar_gas_scrubber")
                .inputFluids(SkufMaterials.ugarGas.getFluid(1000))
                .inputFluids(GTMaterials.Water.getFluid(500))
                .outputFluids(SkufMaterials.dilutedSweat.getFluid(1500))
                .duration(160)
                .EUt(GTValues.VA[GTValues.EV])
                .save(provider);

        GTRecipeTypes.CHEMICAL_RECIPES.recipeBuilder("hide_sweat_with_denial")
                .inputFluids(SkufMaterials.sweat.getFluid(1000))
                .inputFluids(SkufMaterials.coolantOfDenial.getFluid(500))
                .outputFluids(SkufMaterials.hiddenSweat.getFluid(1000))
                .duration(240)
                .EUt(GTValues.V[GTValues.HV])
                .save(provider);
    }

    private static void vanillaCrafting(Consumer<FinishedRecipe> provider) {
        // ── Hulls: smoldering_pukan ───────────────────────────────────────────
        // LV Smoldering Pukan
        VanillaRecipeHelper.addShapedRecipe(provider, true, "hull_smoldering_pukan_lv",
                SkufComponentMachines.SMOLDERING_PUKAN[GTValues.LV].asStack(),
                "PPP", "PCP", "PPP",
                'P', ChemicalHelper.get(plate, SkufMaterials.honestSteel),
                'C', ChemicalHelper.get(cableGtSingle, SkufMaterials.honestSteel));

        // MV Smoldering Pukan
        VanillaRecipeHelper.addShapedRecipe(provider, true, "hull_smoldering_pukan_mv",
                SkufComponentMachines.SMOLDERING_PUKAN[GTValues.MV].asStack(),
                "PPP", "PCP", "PPP",
                'P', ChemicalHelper.get(plate, SkufMaterials.pokhuit),
                'C', ChemicalHelper.get(cableGtSingle, SkufMaterials.pokhuit));

        // HV Smoldering Pukan
        VanillaRecipeHelper.addShapedRecipe(provider, true, "hull_smoldering_pukan_hv",
                SkufComponentMachines.SMOLDERING_PUKAN[GTValues.HV].asStack(),
                "PPP", "PCP", "PPP",
                'P', ChemicalHelper.get(plate, SkufMaterials.crystallizedDodikSweat),
                'C', ChemicalHelper.get(cableGtSingle, SkufMaterials.crystallizedDodikSweat));

        // ── LV Machines ───────────────────────────────────────────────────────
        // LV CNC Machine
        VanillaRecipeHelper.addShapedRecipe(provider, true, "machine_cnc_lv",
                SkufSingleblockMachines.CNC_MACHINE[GTValues.LV].asStack(),
                " C ", "BHB", " S ",
                'C', SkufItems.DODIK_CIRCUIT_BASIC.asStack(),
                'B', ChemicalHelper.get(cableGtSingle, SkufMaterials.honestSteel),
                'H', SkufComponentMachines.SMOLDERING_PUKAN[GTValues.LV].asStack(),
                'S', SkufItems.CNC_BIT.asStack());

        // LV Normis Filtration
        VanillaRecipeHelper.addShapedRecipe(provider, true, "machine_normis_filtration_lv",
                SkufSingleblockMachines.NORMIS_FILTRATION_MACHINE[GTValues.LV].asStack(),
                " C ", "BHB", " S ",
                'C', SkufItems.DODIK_CIRCUIT_BASIC.asStack(),
                'B', ChemicalHelper.get(cableGtSingle, SkufMaterials.honestSteel),
                'H', SkufComponentMachines.SMOLDERING_PUKAN[GTValues.LV].asStack(),
                'S', ChemicalHelper.get(dust, SkufMaterials.normieDust));

        // LV Pot Distillery
        VanillaRecipeHelper.addShapedRecipe(provider, true, "machine_pot_distillery_lv",
                SkufSingleblockMachines.POT_DISTILLERY[GTValues.LV].asStack(),
                " C ", "BHB", " S ",
                'C', SkufItems.DODIK_CIRCUIT_BASIC.asStack(),
                'B', ChemicalHelper.get(cableGtSingle, SkufMaterials.honestSteel),
                'H', SkufComponentMachines.SMOLDERING_PUKAN[GTValues.LV].asStack(),
                'S', ChemicalHelper.get(frameGt, SkufMaterials.skufit));

        // LV Vibe Stabilizer
        VanillaRecipeHelper.addShapedRecipe(provider, true, "machine_vibe_stabilizer_lv",
                SkufSingleblockMachines.VIBE_STABILIZER[GTValues.LV].asStack(),
                " C ", "BHB", " S ",
                'C', SkufItems.DODIK_CIRCUIT_BASIC.asStack(),
                'B', ChemicalHelper.get(cableGtSingle, SkufMaterials.honestSteel),
                'H', SkufComponentMachines.SMOLDERING_PUKAN[GTValues.LV].asStack(),
                'S', ChemicalHelper.get(frameGt, SkufMaterials.pokhuit));

        // ── MV Machines ───────────────────────────────────────────────────────
        // MV CNC Machine
        VanillaRecipeHelper.addShapedRecipe(provider, true, "machine_cnc_mv",
                SkufSingleblockMachines.CNC_MACHINE[GTValues.MV].asStack(),
                " C ", "BHB", " S ",
                'C', SkufItems.DODIK_CIRCUIT_ADVANCED.asStack(),
                'B', ChemicalHelper.get(cableGtSingle, SkufMaterials.pokhuit),
                'H', SkufComponentMachines.SMOLDERING_PUKAN[GTValues.MV].asStack(),
                'S', SkufItems.CNC_BIT.asStack());

        // MV Normis Filtration
        VanillaRecipeHelper.addShapedRecipe(provider, true, "machine_normis_filtration_mv",
                SkufSingleblockMachines.NORMIS_FILTRATION_MACHINE[GTValues.MV].asStack(),
                " C ", "BHB", " S ",
                'C', SkufItems.DODIK_CIRCUIT_ADVANCED.asStack(),
                'B', ChemicalHelper.get(cableGtSingle, SkufMaterials.pokhuit),
                'H', SkufComponentMachines.SMOLDERING_PUKAN[GTValues.MV].asStack(),
                'S', ChemicalHelper.get(dust, SkufMaterials.normieDust));

        // MV Pot Distillery
        VanillaRecipeHelper.addShapedRecipe(provider, true, "machine_pot_distillery_mv",
                SkufSingleblockMachines.POT_DISTILLERY[GTValues.MV].asStack(),
                " C ", "BHB", " S ",
                'C', SkufItems.DODIK_CIRCUIT_ADVANCED.asStack(),
                'B', ChemicalHelper.get(cableGtSingle, SkufMaterials.pokhuit),
                'H', SkufComponentMachines.SMOLDERING_PUKAN[GTValues.MV].asStack(),
                'S', ChemicalHelper.get(frameGt, SkufMaterials.skufit));

        // MV Vibe Stabilizer
        VanillaRecipeHelper.addShapedRecipe(provider, true, "machine_vibe_stabilizer_mv",
                SkufSingleblockMachines.VIBE_STABILIZER[GTValues.MV].asStack(),
                " C ", "BHB", " S ",
                'C', SkufItems.DODIK_CIRCUIT_ADVANCED.asStack(),
                'B', ChemicalHelper.get(cableGtSingle, SkufMaterials.pokhuit),
                'H', SkufComponentMachines.SMOLDERING_PUKAN[GTValues.MV].asStack(),
                'S', ChemicalHelper.get(frameGt, SkufMaterials.pokhuit));
    }

    private static void exampleRecipes(Consumer<FinishedRecipe> provider) {
        GTRecipeTypes.ASSEMBLER_RECIPES.recipeBuilder("skufizator")
                .inputItems(frameGt, SkufMaterials.skufit, 4)
                .inputItems(block, SkufMaterials.correctMatter, 3)
                .inputItems(screw, GTMaterials.Electrum, 2)
                .circuitMeta(6)
                .outputItems(SkufMultiblockMachines.SKUFIZATOR.asStack())
                .duration(600)
                .EUt(480)
                .save(provider);
    }
}
