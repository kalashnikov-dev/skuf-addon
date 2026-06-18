package com.arturgpt.skufaddon.common.data;

import com.arturgpt.skufaddon.SkufAddon;
import com.arturgpt.skufaddon.common.machine.multiblock.sauna.SaunaEgoraMachine;
import com.arturgpt.skufaddon.common.machine.multiblock.sauna.SaunaEgoraPatterns;

import com.gregtechceu.gtceu.GTCEu;
import com.gregtechceu.gtceu.api.GTValues;
import com.gregtechceu.gtceu.api.data.RotationState;
import com.gregtechceu.gtceu.api.machine.MultiblockMachineDefinition;
import com.gregtechceu.gtceu.api.machine.multiblock.WorkableElectricMultiblockMachine;
import com.gregtechceu.gtceu.api.pattern.FactoryBlockPattern;
import com.gregtechceu.gtceu.api.pattern.MultiblockShapeInfo;
import com.gregtechceu.gtceu.api.pattern.Predicates;
import com.gregtechceu.gtceu.common.data.GTBlocks;
import com.gregtechceu.gtceu.common.data.GTRecipeTypes;

import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.block.Blocks;

import java.util.List;

import static com.gregtechceu.gtceu.api.pattern.Predicates.*;
import static com.gregtechceu.gtceu.common.data.GTMachines.*;
import static com.gregtechceu.gtceu.common.data.GTRecipeModifiers.BATCH_MODE;
import static com.gregtechceu.gtceu.common.data.GTRecipeModifiers.OC_NON_PERFECT_SUBTICK;

public class SkufMultiblockMachines {

    private static final int SKUFIZATOR_HATCH_TIER = 2;

    private static final net.minecraft.resources.ResourceLocation SKUFIZATOR_CASING = GTCEu
            .id("block/casings/solid/machine_casing_inert_ptfe");

    private static final net.minecraft.resources.ResourceLocation SAUNA_CASING = GTCEu
            .id("block/casings/cleanroom/plascrete");

    public static MultiblockMachineDefinition SKUFIZATOR;
    public static MultiblockMachineDefinition SAUNA_EGORA;

    public static void init() {
        initSkufizator();
        initSaunaEgora();
    }

    private static void initSkufizator() {
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
                .shapeInfos(SkufMultiblockMachines::skufizatorShapeInfos)
                .workableCasingModel(
                        SKUFIZATOR_CASING,
                        SkufAddon.id("block/multiblock/skufizator"))
                .tooltips(Component.translatable("skufaddon.multiblock.skufizator.tooltip.structure"))
                .register();
    }

    private static void initSaunaEgora() {
        SAUNA_EGORA = SkufAddon.REGISTRATE
                .multiblock("sauna_egora", SaunaEgoraMachine::new)
                .rotationState(RotationState.NON_Y_AXIS)
                .allowExtendedFacing(false)
                .recipeType(GTRecipeTypes.DUMMY_RECIPES)
                .appearanceBlock(GTBlocks.PLASTCRETE)
                .pattern(SaunaEgoraPatterns::create)
                .shapeInfos(SkufMultiblockMachines::saunaShapeInfos)
                .workableCasingModel(
                        SAUNA_CASING,
                        SkufAddon.id("block/multiblock/sauna_egora"))
                .tooltips(
                        Component.translatable("skufaddon.multiblock.sauna_egora.tooltip.0"),
                        Component.translatable("skufaddon.multiblock.sauna_egora.tooltip.1"),
                        Component.translatable("skufaddon.multiblock.sauna_egora.tooltip.structure"))
                .register();
    }

    private static List<MultiblockShapeInfo> saunaShapeInfos(MultiblockMachineDefinition definition) {
        return List.of(
                saunaShapeInfo(definition, Direction.SOUTH),
                saunaShapeInfo(definition, Direction.NORTH),
                saunaShapeInfo(definition, Direction.EAST),
                saunaShapeInfo(definition, Direction.WEST));
    }

    private static MultiblockShapeInfo saunaShapeInfo(MultiblockMachineDefinition definition,
                                                      Direction controllerFacing) {
        var base = MultiblockShapeInfo.builder()
                .where('C', definition, controllerFacing)
                .where('P', GTBlocks.PLASTCRETE.getDefaultState())
                .where('F', SkufBlocks.pokhuitFrame().getDefaultState())
                .where('E', ENERGY_INPUT_HATCH[GTValues.EV], controllerFacing)
                .where('M', MAINTENANCE_HATCH, controllerFacing)
                .where('O', FLUID_EXPORT_HATCH[GTValues.EV], controllerFacing)
                .where('#', Blocks.AIR.defaultBlockState());

        String[] floor = SaunaEgoraPatterns.floorShapeLayer();
        String[] wall = SaunaEgoraPatterns.wallLayer();
        String[] rim = SaunaEgoraPatterns.rimLayer();

        var builder = base;
        for (int i = 0; i < SaunaEgoraPatterns.DEPTH; i++) {
            builder = builder.aisle(floor[i], wall[i], rim[i]);
        }
        return builder.build();
    }

    private static List<MultiblockShapeInfo> skufizatorShapeInfos(MultiblockMachineDefinition definition) {
        var base = MultiblockShapeInfo.builder()
                .where('S', definition, Direction.SOUTH)
                .where('P', SkufBlocks.PUKAN_CORE_CASING.getDefaultState())
                .where('C', SkufBlocks.skufitFrame().getDefaultState())
                .where('I', ITEM_IMPORT_BUS[SKUFIZATOR_HATCH_TIER], Direction.NORTH)
                .where('O', ITEM_EXPORT_BUS[SKUFIZATOR_HATCH_TIER], Direction.SOUTH)
                .where('E', ENERGY_INPUT_HATCH[SKUFIZATOR_HATCH_TIER], Direction.UP)
                .where('M', MAINTENANCE_HATCH, Direction.DOWN);

        return List.of(
                base.shallowCopy()
                        .aisle("CCC", "CCC", "CCC")
                        .aisle("CPC", "CPC", "CPC")
                        .aisle("OCE", "ISC", "CMC")
                        .build(),
                base.shallowCopy()
                        .aisle("EIC", "CCC", "CMC")
                        .aisle("CPC", "CPC", "CPC")
                        .aisle("CCC", "CSC", "CCC")
                        .build(),
                base.shallowCopy()
                        .aisle("CCC", "CCC", "CCC")
                        .aisle("IPC", "CPC", "OMC")
                        .aisle("CCC", "CSC", "CCC")
                        .build(),
                base.shallowCopy()
                        .aisle("EIC", "CCC", "CMC")
                        .aisle("CPC", "CPC", "CPC")
                        .aisle("OCC", "CSC", "CCC")
                        .build());
    }
}
