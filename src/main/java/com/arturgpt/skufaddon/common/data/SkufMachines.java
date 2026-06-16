package com.arturgpt.skufaddon.common.data;

import com.arturgpt.skufaddon.SkufAddon;
import com.arturgpt.skufaddon.common.machine.tilt.SkufTiltMachine;

import com.gregtechceu.gtceu.api.GTValues;
import com.gregtechceu.gtceu.api.machine.MachineDefinition;
import com.gregtechceu.gtceu.api.machine.SimpleTieredMachine;

import static com.gregtechceu.gtceu.common.data.machines.GTMachineUtils.ELECTRIC_TIERS;

public class SkufMachines {

    public static final MachineDefinition[] NORMIS_FILTRATION_MACHINE = new MachineDefinition[GTValues.TIER_COUNT];

    public static void init() {
        for (int tier : ELECTRIC_TIERS) {
            String name = GTValues.VN[tier].toLowerCase() + "_normis_filtration_machine";

            NORMIS_FILTRATION_MACHINE[tier] = SkufAddon.REGISTRATE
                    .machine(name, holder -> new SkufTiltMachine(holder, tier))
                    .langValue(GTValues.VNF[tier] + " Normis Filtration Machine")
                    .recipeType(SkufRecipeTypes.NORMIS_FILTRATION_RECIPES)
                    .editableUI(SimpleTieredMachine.EDITABLE_UI_CREATOR.apply(
                            SkufAddon.id("normis_filtration_machine"),
                            SkufRecipeTypes.NORMIS_FILTRATION_RECIPES))
                    .workableTieredHullModel(SkufAddon.id("block/machines/normis_filtration_machine"))
                    .register();
        }
    }
}
