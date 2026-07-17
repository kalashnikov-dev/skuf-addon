package com.arturgpt.skufaddon.common.machine.multiblock.sauna;

import com.arturgpt.skufaddon.api.machine.ISaunaProvider;
import com.arturgpt.skufaddon.api.machine.ISaunaReceiver;
import com.arturgpt.skufaddon.common.data.SkufBlocks;

import com.gregtechceu.gtceu.api.GTValues;
import com.gregtechceu.gtceu.api.machine.IMachineBlockEntity;
import com.gregtechceu.gtceu.api.machine.MetaMachine;
import com.gregtechceu.gtceu.api.machine.MultiblockMachineDefinition;
import com.gregtechceu.gtceu.api.machine.multiblock.PartAbility;
import com.gregtechceu.gtceu.api.pattern.BlockPattern;
import com.gregtechceu.gtceu.api.pattern.FactoryBlockPattern;
import com.gregtechceu.gtceu.api.pattern.TraceabilityPredicate;
import com.gregtechceu.gtceu.api.pattern.util.RelativeDirection;
import com.gregtechceu.gtceu.common.data.GTBlocks;
import com.gregtechceu.gtceu.config.ConfigHolder;

import com.lowdragmc.lowdraglib.utils.BlockInfo;

import net.minecraft.network.chat.Component;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;

import com.google.common.collect.Sets;

import java.util.Set;

import static com.gregtechceu.gtceu.api.pattern.Predicates.abilities;
import static com.gregtechceu.gtceu.api.pattern.Predicates.ability;
import static com.gregtechceu.gtceu.api.pattern.Predicates.blocks;
import static com.gregtechceu.gtceu.api.pattern.Predicates.controller;

/**
 * Sauna Egora: 18 x 11 footprint, 3 blocks tall.
 * <p>
 * Axes: long side (18) along {@link RelativeDirection#FRONT}/{@link RelativeDirection#BACK}
 * behind the controller; short side (11) along {@link RelativeDirection#LEFT}/{@link RelativeDirection#RIGHT}.
 * Place the controller facing outward — the cavity extends behind it.
 */
public final class SaunaEgoraPatterns {

    public static final int DEPTH = 11;

    private SaunaEgoraPatterns() {}

    public static BlockPattern create(MultiblockMachineDefinition definition) {
        String[] floor = floorLayer();
        String[] wall = wallLayer();
        String[] rim = rimLayer();

        // FRONT = long axis (18 chars, cavity behind controller), LEFT = short axis (11 aisles).
        FactoryBlockPattern pattern = FactoryBlockPattern.start(
                RelativeDirection.FRONT, RelativeDirection.UP, RelativeDirection.LEFT);
        for (int i = 0; i < DEPTH; i++) {
            pattern = pattern.aisle(floor[i], wall[i], rim[i]);
        }

        return pattern
                .where('C', controller(blocks(definition.getBlock())))
                .where('P', casing())
                .where('F', blocks(SkufBlocks.pokhuitFrame().get()))
                .where('#', innerPredicate())
                .build();
    }

    /** Bottom layer rows (one per depth slice). */
    public static String[] floorLayer() {
        return new String[] {
                "                  ",
                " PPPPPPPPPPPPPPPP ",
                " PPPPPPPPPPPPPPPP ",
                " PPPPPPPPPPPPPPPP ",
                " PPPPPPPPPPPPPPPP ",
                " PPPPPPPPPPPPPFPC ",
                " PPPPPPPPPPPPPPPP ",
                " PPPPPPPPPPPPPPPP ",
                " PPPPPPPPPPPPPPPP ",
                " PPPPPPPPPPPPPPPP ",
                "                  ",
        };
    }

    /** EMI / JEI preview floor with example hatch positions. */
    public static String[] floorShapeLayer() {
        return new String[] {
                "                  ",
                " PPPPPPPPPPPPPPPP ",
                " PPPPPPPPPPPPPPPP ",
                " PPPPPPPPPPPPPPPP ",
                " PPPPPPPPPPPPPPPP ",
                " PPPPPPPPPDIOEFMC ",
                " PPPPPPPPPPPPPPPP ",
                " PPPPPPPPPPPPPPPP ",
                " PPPPPPPPPPPPPPPP ",
                " PPPPPPPPPPPPPPPP ",
                "                  ",
        };
    }

    /** Middle layer rows (one per depth slice). */
    public static String[] wallLayer() {
        return new String[] {
                "                  ",
                " PPPPPPPPPPPPPPPP ",
                " P##############P ",
                " P##############P ",
                " P##############P ",
                " P##############P ",
                " P##############P ",
                " P##############P ",
                " P##############P ",
                " PPPPPPPPPPPPPPPP ",
                "                  ",
        };
    }

    /** Top layer rows (one per depth slice). */
    public static String[] rimLayer() {
        return new String[] {
                " PPPPPPPPPPPPPPPP ",
                "PP              PP",
                "P                P",
                "P                P",
                "P                P",
                "P                P",
                "P                P",
                "P                P",
                "P                P",
                "PP              PP",
                " PPPPPPPPPPPPPPPP ",
        };
    }

    private static TraceabilityPredicate casing() {
        return blocks(GTBlocks.PLASTCRETE.get())
                .or(ability(PartAbility.INPUT_ENERGY, GTValues.tiersBetween(GTValues.EV, GTValues.MAX))
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(3)
                        .addTooltips(Component.translatable("skufaddon.multiblock.sauna_egora.insufficient_tier")))
                .or(abilities(PartAbility.MAINTENANCE)
                        .setMinGlobalLimited(ConfigHolder.INSTANCE.machines.enableMaintenance ? 1 : 0)
                        .setMaxGlobalLimited(1))
                .or(abilities(PartAbility.EXPORT_FLUIDS)
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(2))
                .or(abilities(PartAbility.IMPORT_FLUIDS)
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(1))
                .or(abilities(PartAbility.PASSTHROUGH_HATCH)
                        .setMinGlobalLimited(1)
                        .setMaxGlobalLimited(16));
    }

    private static TraceabilityPredicate innerPredicate() {
        return new TraceabilityPredicate(blockWorldState -> {
            Set<ISaunaReceiver> receivers = blockWorldState.getMatchContext()
                    .getOrCreate("saunaReceiver", Sets::newHashSet);
            BlockEntity blockEntity = blockWorldState.getTileEntity();
            if (blockEntity instanceof IMachineBlockEntity machineBlockEntity) {
                MetaMachine machine = machineBlockEntity.getMetaMachine();
                if (machine instanceof ISaunaProvider) {
                    return false;
                }
                if (machine instanceof ISaunaReceiver receiver) {
                    receivers.add(receiver);
                }
            }
            return true;
        }, () -> new BlockInfo[] { BlockInfo.fromBlockState(Blocks.AIR.defaultBlockState()) }) {

            @Override
            public boolean isAny() {
                return true;
            }

            @Override
            public boolean addCache() {
                return true;
            }
        };
    }
}
