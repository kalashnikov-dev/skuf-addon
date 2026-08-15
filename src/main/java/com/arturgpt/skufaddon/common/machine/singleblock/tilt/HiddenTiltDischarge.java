package com.arturgpt.skufaddon.common.machine.singleblock.tilt;

import com.arturgpt.skufaddon.common.config.SkufBalanceConfig;
import com.gregtechceu.gtceu.api.GTValues;
import com.gregtechceu.gtceu.api.machine.MetaMachine;
import com.gregtechceu.gtceu.api.machine.feature.IExplosionMachine;
import com.gregtechceu.gtceu.api.machine.feature.ITieredMachine;
import com.gregtechceu.gtceu.common.blockentity.CableBlockEntity;
import com.gregtechceu.gtceu.common.machine.electric.BatteryBufferMachine;
import com.gregtechceu.gtceu.common.machine.electric.ChargerMachine;
import com.gregtechceu.gtceu.common.machine.electric.ConverterMachine;
import com.gregtechceu.gtceu.common.machine.electric.TransformerMachine;
import com.gregtechceu.gtceu.common.machine.multiblock.electric.ActiveTransformerMachine;
import com.gregtechceu.gtceu.common.machine.multiblock.part.DiodePartMachine;
import com.gregtechceu.gtceu.config.ConfigHolder;
import com.gregtechceu.gtceu.utils.GTUtil;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Reuses GTCEu cable melt ({@link CableBlockEntity#applyHeat(int)}) and
 * {@link IExplosionMachine#doExplosion(float)} for attached energy gear.
 */
final class HiddenTiltDischarge {

    private static final int MAX_CABLE_WALK = 256;

    private HiddenTiltDischarge() {}

    static void burnAttachedCables(MetaMachine machine) {
        Level level = machine.getLevel();
        if (level == null || level.isClientSide) {
            return;
        }
        int limit = SkufBalanceConfig.HIDDEN_TILT_CABLE_BURN_COUNT != null ?
                SkufBalanceConfig.HIDDEN_TILT_CABLE_BURN_COUNT.get() : 8;
        List<BlockPos> cables = collectAttachedCables(level, machine.getPos());
        int end = Math.min(limit, cables.size());
        for (int i = 0; i < end; i++) {
            if (level.getBlockEntity(cables.get(i)) instanceof CableBlockEntity cable) {
                cable.applyHeat(CableBlockEntity.getMeltTemp());
            }
        }
    }

    static void explodeAttachedEnergyGear(MetaMachine source) {
        Level level = source.getLevel();
        if (level == null || level.isClientSide) {
            return;
        }
        List<BlockPos> cables = collectAttachedCables(level, source.getPos());
        Set<BlockPos> cableSet = new HashSet<>(cables);
        Set<BlockPos> candidates = new HashSet<>();
        addNeighbors(candidates, source.getPos());
        for (BlockPos cablePos : cables) {
            addNeighbors(candidates, cablePos);
        }
        candidates.remove(source.getPos());
        candidates.removeAll(cableSet);

        long voltage = source instanceof ITieredMachine tiered ? GTValues.V[tiered.getTier()] : GTValues.V[GTValues.LV];
        float power = GTUtil.getExplosionPower(voltage);

        for (BlockPos pos : candidates) {
            MetaMachine neighbor = MetaMachine.getMachine(level, pos);
            if (neighbor == null || neighbor == source || !isEnergyInfrastructure(neighbor)) {
                continue;
            }
            explode(neighbor, level, pos, power);
        }
    }

    private static void explode(MetaMachine machine, Level level, BlockPos pos, float power) {
        if (machine instanceof IExplosionMachine explosive) {
            explosive.doExplosion(power);
            return;
        }
        level.removeBlock(pos, false);
        level.explode(null, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, power,
                ConfigHolder.INSTANCE.machines.doesExplosionDamagesTerrain ?
                        Level.ExplosionInteraction.BLOCK : Level.ExplosionInteraction.NONE);
    }

    private static boolean isEnergyInfrastructure(MetaMachine machine) {
        return machine instanceof TransformerMachine
                || machine instanceof BatteryBufferMachine
                || machine instanceof ChargerMachine
                || machine instanceof ConverterMachine
                || machine instanceof DiodePartMachine
                || machine instanceof ActiveTransformerMachine;
    }

    /** BFS from the machine: nearest cables first (order preserved). */
    private static List<BlockPos> collectAttachedCables(Level level, BlockPos origin) {
        List<BlockPos> ordered = new ArrayList<>();
        Set<BlockPos> visited = new HashSet<>();
        ArrayDeque<BlockPos> queue = new ArrayDeque<>();
        for (Direction side : GTUtil.DIRECTIONS) {
            BlockPos next = origin.relative(side);
            if (level.getBlockEntity(next) instanceof CableBlockEntity) {
                queue.add(next);
            }
        }
        while (!queue.isEmpty() && ordered.size() < MAX_CABLE_WALK) {
            BlockPos pos = queue.removeFirst();
            if (!visited.add(pos)) {
                continue;
            }
            BlockEntity be = level.getBlockEntity(pos);
            if (!(be instanceof CableBlockEntity cable)) {
                visited.remove(pos);
                continue;
            }
            ordered.add(pos);
            for (Direction side : GTUtil.DIRECTIONS) {
                if (!cable.isConnected(side)) {
                    continue;
                }
                BlockPos next = pos.relative(side);
                if (!visited.contains(next) && level.getBlockEntity(next) instanceof CableBlockEntity) {
                    queue.add(next);
                }
            }
        }
        return ordered;
    }

    private static void addNeighbors(Set<BlockPos> out, BlockPos origin) {
        for (Direction side : GTUtil.DIRECTIONS) {
            out.add(origin.relative(side));
        }
    }
}
