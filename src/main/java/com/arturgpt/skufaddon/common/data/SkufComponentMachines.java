package com.arturgpt.skufaddon.common.data;

import com.arturgpt.skufaddon.SkufAddon;

import com.gregtechceu.gtceu.api.GTValues;
import com.gregtechceu.gtceu.api.data.RotationState;
import com.gregtechceu.gtceu.api.machine.MachineDefinition;
import com.gregtechceu.gtceu.api.machine.multiblock.PartAbility;
import com.gregtechceu.gtceu.common.data.machines.GTMachineUtils;
import com.gregtechceu.gtceu.common.machine.electric.HullMachine;

import net.minecraft.network.chat.Component;

public final class SkufComponentMachines {

    public static final MachineDefinition[] SMOLDERING_PUKAN = new MachineDefinition[GTValues.TIER_COUNT];

    private SkufComponentMachines() {}

    public static void init() {
        MachineDefinition[] registered = GTMachineUtils.registerTieredMachines(
                SkufAddon.REGISTRATE,
                "smoldering_pukan",
                HullMachine::new,
                (tier, builder) -> builder
                        .rotationState(RotationState.ALL)
                        .overlayTieredHullModel("smoldering_pukan")
                        .abilities(PartAbility.PASSTHROUGH_HATCH)
                        .tooltips(Component.translatable("gtceu.machine.hull.tooltip"))
                        .register(),
                GTValues.tiersBetween(GTValues.LV, GTValues.UHV));
        System.arraycopy(registered, 0, SMOLDERING_PUKAN, 0, GTValues.TIER_COUNT);
    }
}
