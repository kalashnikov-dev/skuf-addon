package com.arturgpt.skufaddon.common.data;

import com.arturgpt.skufaddon.SkufAddon;

import com.gregtechceu.gtceu.GTCEu;
import com.gregtechceu.gtceu.api.data.RotationState;
import com.gregtechceu.gtceu.api.machine.MultiblockMachineDefinition;
import com.gregtechceu.gtceu.api.machine.multiblock.WorkableElectricMultiblockMachine;
import com.gregtechceu.gtceu.api.pattern.FactoryBlockPattern;
import com.gregtechceu.gtceu.api.pattern.MultiblockShapeInfo;
import com.gregtechceu.gtceu.api.pattern.Predicates;

import net.minecraft.core.Direction;

import java.util.List;

import static com.gregtechceu.gtceu.api.pattern.Predicates.*;
import static com.gregtechceu.gtceu.common.data.GTMachines.*;
import static com.gregtechceu.gtceu.common.data.GTRecipeModifiers.BATCH_MODE;
import static com.gregtechceu.gtceu.common.data.GTRecipeModifiers.OC_NON_PERFECT_SUBTICK;

public class SkufMultiblockMachines {

    public static MultiblockMachineDefinition SKUFIZATOR;

    public static void init() {
        SKUFIZATOR = SkufAddon.REGISTRATE
                .multiblock("skufizator", WorkableElectricMultiblockMachine::new)
                .rotationState(RotationState.ALL)
                .recipeType(SkufRecipeTypes.SKUFIZATION_RECIPES)
                .recipeModifiers(OC_NON_PERFECT_SUBTICK, BATCH_MODE)
                .appearanceBlock(SkufBlocks.skufitFrame())
                .pattern(definition -> FactoryBlockPattern.start()
                        .aisle("CCC", "CCC", "CCC")
                        .aisle("CPC", "CPC", "CPC")
                        .aisle("CCC", "CSC", "CCC")
                        .where('S', controller(blocks(definition.getBlock())))
                        .where('P', blocks(SkufBlocks.PUKAN_CORE_CASING.get()))
                        .where('C', blocks(SkufBlocks.skufitFrame().get()).setMinGlobalLimited(12)
                                .or(Predicates.autoAbilities(definition.getRecipeTypes()))
                                .or(Predicates.autoAbilities(true, false, false)))
                        .build())
                .shapeInfos(definition -> List.of(
                        MultiblockShapeInfo.builder()
                                .aisle("CCC", "CCC", "CCC")
                                .aisle("CPC", "CPC", "CPC")
                                .aisle("OCE", "ISC", "CMC")
                                .where('S', definition, Direction.SOUTH)
                                .where('P', SkufBlocks.PUKAN_CORE_CASING.getDefaultState())
                                .where('C', SkufBlocks.skufitFrame().getDefaultState())
                                .where('I', ITEM_IMPORT_BUS[2], Direction.NORTH)
                                .where('O', ITEM_EXPORT_BUS[2], Direction.SOUTH)
                                .where('E', ENERGY_INPUT_HATCH[2], Direction.UP)
                                .where('M', MAINTENANCE_HATCH, Direction.DOWN)
                                .build()))
                .workableCasingModel(
                        GTCEu.id("block/material_sets/dull/frame_gt"),
                        SkufAddon.id("block/multiblock/skufizator"))
                .register();
    }
}
