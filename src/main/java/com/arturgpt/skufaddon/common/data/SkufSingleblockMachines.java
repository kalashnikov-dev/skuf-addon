package com.arturgpt.skufaddon.common.data;

import com.arturgpt.skufaddon.SkufAddon;
import com.arturgpt.skufaddon.common.machine.singleblock.tilt.SkufTiltMachine;

import com.gregtechceu.gtceu.api.GTValues;
import com.gregtechceu.gtceu.api.machine.MachineDefinition;
import com.gregtechceu.gtceu.api.machine.SimpleTieredMachine;
import com.gregtechceu.gtceu.api.recipe.GTRecipeType;

public class SkufSingleblockMachines {

    public static final MachineDefinition[] NORMIS_FILTRATION_MACHINE = new MachineDefinition[GTValues.TIER_COUNT];
    public static final MachineDefinition[] CNC_MACHINE = new MachineDefinition[GTValues.TIER_COUNT];
    public static final MachineDefinition[] POT_DISTILLERY = new MachineDefinition[GTValues.TIER_COUNT];
    public static final MachineDefinition[] VIBE_STABILIZER = new MachineDefinition[GTValues.TIER_COUNT];

    public static void init() {
        registerTiltMachines(NORMIS_FILTRATION_MACHINE, "normis_filtration_machine",
                SkufRecipeTypes.NORMIS_FILTRATION_RECIPES, " Normis Filtration Machine");
        registerTiltMachines(CNC_MACHINE, "cnc_machine", SkufRecipeTypes.CNC_RECIPES, " CNC Machine");
        registerTiltMachines(POT_DISTILLERY, "pot_distillery", SkufRecipeTypes.POT_DISTILLERY_RECIPES,
                " Pot Distillery");
        registerTiltMachines(VIBE_STABILIZER, "vibe_stabilizer", SkufRecipeTypes.VIBE_STABILIZER_RECIPES,
                " Vibe Stabilizer");
    }

    private static void registerTiltMachines(MachineDefinition[] target, String baseName,
                                             GTRecipeType recipeType, String langSuffix) {
        for (int tier : GTValues.tiersBetween(GTValues.LV, GTValues.UHV)) {
            String name = GTValues.VN[tier].toLowerCase() + "_" + baseName;
            target[tier] = SkufAddon.REGISTRATE
                    .machine(name, holder -> new SkufTiltMachine(holder, tier))
                    .langValue(GTValues.VNF[tier] + langSuffix)
                    .recipeType(recipeType)
                    .editableUI(SimpleTieredMachine.EDITABLE_UI_CREATOR.apply(
                            SkufAddon.id(baseName),
                            recipeType))
                    .workableTieredHullModel(SkufAddon.id("block/machines/" + baseName))
                    .register();
        }
    }
}
