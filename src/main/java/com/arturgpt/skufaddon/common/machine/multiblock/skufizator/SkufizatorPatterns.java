package com.arturgpt.skufaddon.common.machine.multiblock.skufizator;

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
import static com.gregtechceu.gtceu.api.pattern.Predicates.air;
import static com.gregtechceu.gtceu.api.pattern.Predicates.blocks;
import static com.gregtechceu.gtceu.api.pattern.Predicates.controller;

/**
 * Skufizator «samovar»: 5×5 bowl of Skufit frames with a Correct Matter column
 * standing on the bowl floor and rising through the rim.
 * <p>
 * Same axis convention as {@link com.arturgpt.skufaddon.common.machine.multiblock.sauna.SaunaEgoraPatterns}:
 * depth along {@link RelativeDirection#FRONT}/{@link RelativeDirection#BACK};
 * width along {@link RelativeDirection#LEFT}/{@link RelativeDirection#RIGHT};
 * height along {@link RelativeDirection#UP}.
 * Place the controller on the front of the bowl, facing outward.
 */
public final class SkufizatorPatterns {

    public static final int WIDTH = 5;
    public static final int DEPTH = 5;
    public static final int HEIGHT = 6;
    public static final int HATCH_TIER = GTValues.MV;

    /** Minimum skufit frames on the bowl (hatches replace some C slots). */
    public static final int MIN_FRAMES = 20;

    private SkufizatorPatterns() {}

    public static BlockPattern create(MultiblockMachineDefinition definition) {
        String[] floor = floorLayer();
        String[] bowl = bowlLayer();
        String[] rim = rimLayer();
        String[] chimney = chimneyTopLayer();

        FactoryBlockPattern pattern = FactoryBlockPattern.start(
                RelativeDirection.FRONT, RelativeDirection.UP, RelativeDirection.LEFT);
        for (int i = 0; i < WIDTH; i++) {
            // Y0 frame floor → Y1–Y2 bowl with P column standing on it → Y3–Y5 chimney top
            pattern = pattern.aisle(
                    floor[i],
                    bowl[i],
                    rim[i],
                    chimney[i],
                    chimney[i],
                    chimney[i]);
        }

        return pattern
                .where('S', controller(blocks(definition.getBlock())))
                .where('C', casing())
                .where('P', blocks(SkufBlocks.correctMatterBlock().get()))
                .where('#', air())
                .build();
    }

    /** Y0 — bowl floor, cut corners. */
    public static String[] floorLayer() {
        return new String[] {
                "#CCC#",
                "CCCCC",
                "CCCCC",
                "CCCCC",
                "#CCC#",
        };
    }

    /**
     * Y1 — hollow bowl wall; Correct Matter column stands on the Y0 frame floor;
     * controller on front center.
     */
    public static String[] bowlLayer() {
        return new String[] {
                "CCCCC",
                "C###C",
                "C#P#S",
                "C###C",
                "CCCCC",
        };
    }

    /** EMI bowl with example hatches on the front rim. */
    public static String[] bowlShapeLayer() {
        return new String[] {
                "CCCCE",
                "C###I",
                "C#P#S",
                "C###O",
                "MCCCF",
        };
    }

    /** Y2 — upper rim with Correct Matter column through the center. */
    public static String[] rimLayer() {
        return new String[] {
                "#CCC#",
                "C###C",
                "C#P#C",
                "C###C",
                "#CCC#",
        };
    }

    /** Y3–Y5 — Correct Matter chimney above the bowl (same center column). */
    public static String[] chimneyTopLayer() {
        return new String[] {
                "#####",
                "#####",
                "##P##",
                "#####",
                "#####",
        };
    }

    /**
     * Bowl casing: skufit frames + required recipe IO (exactly one each) + energy + maintenance.
     * Same min/max style as Sauna/Razbor — no {@code setExactLimit}.
     */
    private static TraceabilityPredicate casing() {
        return blocks(SkufBlocks.skufitFrame().get()).setMinGlobalLimited(MIN_FRAMES)
                .or(abilities(PartAbility.IMPORT_ITEMS)
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(1))
                .or(abilities(PartAbility.IMPORT_FLUIDS)
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(1))
                .or(abilities(PartAbility.EXPORT_ITEMS)
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(1))
                .or(abilities(PartAbility.INPUT_ENERGY)
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(2))
                .or(abilities(PartAbility.MAINTENANCE)
                        .setMinGlobalLimited(ConfigHolder.INSTANCE.machines.enableMaintenance ? 1 : 0)
                        .setMaxGlobalLimited(1));
    }
}
