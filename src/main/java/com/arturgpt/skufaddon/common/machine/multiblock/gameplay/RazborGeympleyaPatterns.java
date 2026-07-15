package com.arturgpt.skufaddon.common.machine.multiblock.gameplay;

import com.arturgpt.skufaddon.common.data.SkufBlocks;

import com.gregtechceu.gtceu.api.GTValues;
import com.gregtechceu.gtceu.api.machine.MultiblockMachineDefinition;
import com.gregtechceu.gtceu.api.machine.multiblock.PartAbility;
import com.gregtechceu.gtceu.api.pattern.BlockPattern;
import com.gregtechceu.gtceu.api.pattern.FactoryBlockPattern;
import com.gregtechceu.gtceu.api.pattern.TraceabilityPredicate;
import com.gregtechceu.gtceu.api.pattern.util.RelativeDirection;
import com.gregtechceu.gtceu.config.ConfigHolder;

import static com.gregtechceu.gtceu.api.pattern.Predicates.abilities;
import static com.gregtechceu.gtceu.api.pattern.Predicates.ability;
import static com.gregtechceu.gtceu.api.pattern.Predicates.blocks;
import static com.gregtechceu.gtceu.api.pattern.Predicates.controller;

/**
 * Gameplay Breakdown: flat widescreen panel — 14 wide × 3 deep × 7 tall.
 * <p>
 * Same axis convention as {@link com.arturgpt.skufaddon.common.machine.multiblock.sauna.SaunaEgoraPatterns}:
 * depth (3) along {@link RelativeDirection#FRONT}/{@link RelativeDirection#BACK} behind the controller;
 * width (14) along {@link RelativeDirection#LEFT}/{@link RelativeDirection#RIGHT};
 * height (7) along {@link RelativeDirection#UP}.
 * <p>
 * Place the controller on the bottom-center of the front face, facing outward — the panel extends left and right.
 */
public final class RazborGeympleyaPatterns {

    public static final int WIDTH = 14;
    public static final int DEPTH = 3;
    public static final int HEIGHT = 7;

    private static final int CONTROLLER_WIDTH = (WIDTH - 1) / 2;

    private RazborGeympleyaPatterns() {}

    public static BlockPattern create(MultiblockMachineDefinition definition) {
        // FRONT = depth (3 chars, panel behind controller), LEFT = width (14 aisles).
        FactoryBlockPattern pattern = FactoryBlockPattern.start(
                RelativeDirection.FRONT, RelativeDirection.UP, RelativeDirection.LEFT);
        for (int w = 0; w < WIDTH; w++) {
            pattern = pattern.aisle(
                    sliceRow(w, 0, false),
                    sliceRow(w, 1, false),
                    sliceRow(w, 2, false),
                    sliceRow(w, 3, false),
                    sliceRow(w, 4, false),
                    sliceRow(w, 5, false),
                    sliceRow(w, 6, false));
        }

        return pattern
                .where('C', controller(blocks(definition.getBlock())))
                .where('P', casing())
                .where('X', blocks(SkufBlocks.brokenMonitorBlock().get()))
                .build();
    }

    /** One width column at a given height: {@code [back][mid][front]} depth slice. */
    public static String sliceRow(int widthIndex, int heightIndex, boolean shape) {
        char back = backCell(widthIndex, heightIndex, shape);
        char mid = screenOrCasing(widthIndex, heightIndex);
        char front = frontCell(widthIndex, heightIndex);
        return "" + back + mid + front;
    }

    private static char backCell(int widthIndex, int heightIndex, boolean shape) {
        if (shape && heightIndex == 0) {
            return switch (widthIndex) {
                case 3 -> 'I';
                case 4 -> 'E';
                case 5 -> 'M';
                case 6 -> 'O';
                default -> 'P';
            };
        }
        return 'P';
    }

    private static char screenOrCasing(int widthIndex, int heightIndex) {
        if (heightIndex >= 1 && heightIndex <= 5 && widthIndex >= 1 && widthIndex <= 12) {
            return 'X';
        }
        return 'P';
    }

    private static char frontCell(int widthIndex, int heightIndex) {
        if (widthIndex == CONTROLLER_WIDTH && heightIndex == 0) {
            return 'C';
        }
        return screenOrCasing(widthIndex, heightIndex);
    }

    private static TraceabilityPredicate casing() {
        return blocks(SkufBlocks.pokhuitFrame().get())
                .or(ability(PartAbility.INPUT_ENERGY, GTValues.tiersBetween(GTValues.HV, GTValues.MAX))
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(2))
                .or(abilities(PartAbility.MAINTENANCE)
                        .setMinGlobalLimited(ConfigHolder.INSTANCE.machines.enableMaintenance ? 1 : 0)
                        .setMaxGlobalLimited(1))
                .or(abilities(PartAbility.IMPORT_ITEMS)
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(2))
                .or(abilities(PartAbility.EXPORT_FLUIDS)
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(2));
    }
}
