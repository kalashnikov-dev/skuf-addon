package com.arturgpt.skufaddon.common.machine.multiblock.proval;

import com.arturgpt.skufaddon.common.data.SkufBlocks;

import com.gregtechceu.gtceu.api.GTValues;
import com.gregtechceu.gtceu.api.machine.MultiblockMachineDefinition;
import com.gregtechceu.gtceu.api.machine.multiblock.PartAbility;
import com.gregtechceu.gtceu.api.pattern.BlockPattern;
import com.gregtechceu.gtceu.api.pattern.FactoryBlockPattern;
import com.gregtechceu.gtceu.api.pattern.TraceabilityPredicate;
import com.gregtechceu.gtceu.api.pattern.util.RelativeDirection;
import com.gregtechceu.gtceu.common.data.GTBlocks;
import com.gregtechceu.gtceu.config.ConfigHolder;

import static com.gregtechceu.gtceu.api.pattern.Predicates.abilities;
import static com.gregtechceu.gtceu.api.pattern.Predicates.ability;
import static com.gregtechceu.gtceu.api.pattern.Predicates.air;
import static com.gregtechceu.gtceu.api.pattern.Predicates.blocks;
import static com.gregtechceu.gtceu.api.pattern.Predicates.controller;

/**
 * Chelyabinsk Proval: open stepped crater / sinkhole — 9×9 footprint, 4 tall.
 * <p>
 * Distinct from Skufizator (bowl+chimney), Sauna (flat pool), Razbor (screen wall).
 * Inspired by GTCEu fusion ring + chemical-bath trough, but descending into a pit.
 * <p>
 * Same axis convention as other skuf multis:
 * {@link RelativeDirection#FRONT}/{@link RelativeDirection#BACK} = depth (string chars, last = front);
 * {@link RelativeDirection#LEFT}/{@link RelativeDirection#RIGHT} = width (aisles);
 * {@link RelativeDirection#UP} = height (aisle layer order).
 * Place the controller on the front rim, facing outward — the crater opens behind/under it.
 */
public final class ChelyabinskProvalPatterns {

    public static final int WIDTH = 9;
    public static final int DEPTH = 9;
    public static final int HEIGHT = 4;
    public static final int HATCH_TIER = GTValues.HV;

    /** Minimum proval concrete on the crater (hatches replace some C slots). */
    /** 76 concrete blocks in the crater; up to 8 hatch slots may replace casing. */
    public static final int MIN_CASINGS = 68;

    private ChelyabinskProvalPatterns() {}

    public static BlockPattern create(MultiblockMachineDefinition definition) {
        String[] floor = floorLayer();
        String[] lower = lowerRingLayer();
        String[] mid = midRingLayer();
        String[] rim = rimLayer();

        FactoryBlockPattern pattern = FactoryBlockPattern.start(
                RelativeDirection.FRONT, RelativeDirection.UP, RelativeDirection.LEFT);
        for (int i = 0; i < WIDTH; i++) {
            pattern = pattern.aisle(floor[i], lower[i], mid[i], rim[i]);
        }

        return pattern
                .where('S', controller(blocks(definition.getBlock())))
                .where('C', casing())
                .where('G', blocks(GTBlocks.CASING_TEMPERED_GLASS.get()))
                .where('#', air())
                .build();
    }

    /**
     * Y0 — pit floor: 3×3 pad with tempered-glass “toxic pool” in the center.
     * String chars: back → front.
     */
    public static String[] floorLayer() {
        return new String[] {
                "#########",
                "#########",
                "#########",
                "###CCC###",
                "###CGC###",
                "###CCC###",
                "#########",
                "#########",
                "#########",
        };
    }

    /** Y1 — lower step: 5×5 ring around the floor pad. */
    public static String[] lowerRingLayer() {
        return new String[] {
                "#########",
                "#########",
                "##CCCCC##",
                "##C###C##",
                "##C###C##",
                "##C###C##",
                "##CCCCC##",
                "#########",
                "#########",
        };
    }

    /** Y2 — mid step: 7×7 ring. */
    public static String[] midRingLayer() {
        return new String[] {
                "#########",
                "#CCCCCCC#",
                "#C#####C#",
                "#C#####C#",
                "#C#####C#",
                "#C#####C#",
                "#C#####C#",
                "#CCCCCCC#",
                "#########",
        };
    }

    /**
     * Y3 — open rim (octagon cut corners), controller on front-center lip.
     * Looking down you see the whole stepped crater.
     */
    public static String[] rimLayer() {
        return new String[] {
                "#CCCCCCC#",
                "C#######C",
                "C#######C",
                "C#######C",
                "C#######S",
                "C#######C",
                "C#######C",
                "C#######C",
                "#CCCCCCC#",
        };
    }

    /** EMI preview rim with example hatch positions on the front lip. */
    public static String[] rimShapeLayer() {
        return new String[] {
                "#CCCCCCC#",
                "C#######C",
                "C#######C",
                "F#######E",
                "C#######S",
                "C#######I",
                "C#######O",
                "C#######M",
                "#CCCCCCC#",
        };
    }

    private static TraceabilityPredicate casing() {
        return blocks(SkufBlocks.CASING_PROVAL_CONCRETE.get()).setMinGlobalLimited(MIN_CASINGS)
                .or(ability(PartAbility.INPUT_ENERGY, GTValues.tiersBetween(GTValues.HV, GTValues.MAX))
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(2))
                .or(abilities(PartAbility.MAINTENANCE)
                        .setMinGlobalLimited(ConfigHolder.INSTANCE.machines.enableMaintenance ? 1 : 0)
                        .setMaxGlobalLimited(1))
                .or(abilities(PartAbility.IMPORT_ITEMS)
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(2))
                .or(abilities(PartAbility.IMPORT_FLUIDS)
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(1))
                .or(abilities(PartAbility.EXPORT_ITEMS)
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(2));
    }
}
