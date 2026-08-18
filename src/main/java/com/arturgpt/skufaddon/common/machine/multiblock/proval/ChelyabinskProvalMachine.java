package com.arturgpt.skufaddon.common.machine.multiblock.proval;

import com.arturgpt.skufaddon.common.config.SkufBalanceConfig;

import com.gregtechceu.gtceu.api.data.chemical.material.properties.HazardProperty;
import com.gregtechceu.gtceu.api.machine.IMachineBlockEntity;
import com.gregtechceu.gtceu.api.machine.TickableSubscription;
import com.gregtechceu.gtceu.api.machine.multiblock.WorkableElectricMultiblockMachine;
import com.gregtechceu.gtceu.api.machine.multiblock.WorkableMultiblockMachine;

import com.lowdragmc.lowdraglib.syncdata.annotation.DescSynced;
import com.lowdragmc.lowdraglib.syncdata.annotation.Persisted;
import com.lowdragmc.lowdraglib.syncdata.field.ManagedFieldHolder;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;

import org.joml.Vector3f;

import java.util.Collection;
import java.util.List;

/**
 * Chelyabinsk Proval radiation:
 * <ul>
 * <li>AABB = formed structure extremes + {@code padding} blocks on every side (incl. up/down)</li>
 * <li>{@link #radiationIntensity} rises while crafting, cools at the same rate when idle</li>
 * <li>No GTCEu chunk zones — purely local volume around the multiblock</li>
 * </ul>
 */
public class ChelyabinskProvalMachine extends WorkableElectricMultiblockMachine {

    protected static final ManagedFieldHolder MANAGED_FIELD_HOLDER = new ManagedFieldHolder(
            ChelyabinskProvalMachine.class, WorkableMultiblockMachine.MANAGED_FIELD_HOLDER);

    private static final DustParticleOptions RAD_PARTICLE = new DustParticleOptions(new Vector3f(0.35f, 1.0f, 0.15f),
            1.6f);

    private static final float DEFAULT_STRENGTH = 100.0f;
    private static final int DEFAULT_INTERVAL = 20;
    private static final int DEFAULT_PADDING = 7;
    private static final float MAX_INTENSITY = 1000.0f;

    @Persisted
    @DescSynced
    private float radiationIntensity;

    private TickableSubscription radiationSubs;

    public ChelyabinskProvalMachine(IMachineBlockEntity holder) {
        super(holder);
    }

    @Override
    public ManagedFieldHolder getFieldHolder() {
        return MANAGED_FIELD_HOLDER;
    }

    public float getRadiationIntensity() {
        return radiationIntensity;
    }

    private float pulseStrength() {
        return SkufBalanceConfig.PROVAL_HAZARD_STRENGTH_PER_PULSE != null ?
                SkufBalanceConfig.PROVAL_HAZARD_STRENGTH_PER_PULSE.get().floatValue() : DEFAULT_STRENGTH;
    }

    private int pulseInterval() {
        return SkufBalanceConfig.PROVAL_HAZARD_PULSE_INTERVAL_TICKS != null ?
                Math.max(1, SkufBalanceConfig.PROVAL_HAZARD_PULSE_INTERVAL_TICKS.get()) : DEFAULT_INTERVAL;
    }

    /** Blocks beyond structure extremes on each axis (N/S/E/W/up/down). */
    private int radiationPadding() {
        return SkufBalanceConfig.PROVAL_HAZARD_LOCAL_RADIUS != null ?
                SkufBalanceConfig.PROVAL_HAZARD_LOCAL_RADIUS.get() : DEFAULT_PADDING;
    }

    @Override
    public void onLoad() {
        super.onLoad();
        if (!isRemote()) {
            radiationSubs = subscribeServerTick(radiationSubs, this::radiationServerTick);
        }
    }

    @Override
    public void onUnload() {
        unsubscribe(radiationSubs);
        radiationSubs = null;
        super.onUnload();
    }

    /**
     * Continuous tick: heat while recipe runs, cool at the same pulse rate when idle,
     * apply zone + particles while charge remains.
     */
    private void radiationServerTick() {
        if (!(getLevel() instanceof ServerLevel serverLevel) || !isFormed()) {
            return;
        }

        int interval = pulseInterval();
        if (getOffsetTimer() % interval != 0) {
            return;
        }

        float pulse = pulseStrength();
        if (isActive()) {
            radiationIntensity = Math.min(MAX_INTENSITY, radiationIntensity + pulse);
        } else if (radiationIntensity > 0) {
            // Cool at the same rate as accumulation.
            radiationIntensity = Math.max(0, radiationIntensity - pulse);
        }

        if (radiationIntensity > 0.01f) {
            applyLocalRadiation(serverLevel);
            spawnRadiationParticles(serverLevel);
        }
    }

    /**
     * Axis-aligned box from outermost non-air structure blocks, expanded by padding
     * on all six sides (matches the top-down “+7 from each face” sketch).
     */
    private AABB radiationZone() {
        return structureBounds(radiationPadding());
    }

    private AABB structureBounds(int padding) {
        int minX = getPos().getX();
        int minY = getPos().getY();
        int minZ = getPos().getZ();
        int maxX = minX;
        int maxY = minY;
        int maxZ = minZ;

        Collection<BlockPos> cache = getMultiblockState().getCache();
        if (cache != null && getLevel() != null) {
            for (BlockPos pos : cache) {
                BlockState state = getLevel().getBlockState(pos);
                if (state.isAir()) {
                    continue;
                }
                minX = Math.min(minX, pos.getX());
                minY = Math.min(minY, pos.getY());
                minZ = Math.min(minZ, pos.getZ());
                maxX = Math.max(maxX, pos.getX());
                maxY = Math.max(maxY, pos.getY());
                maxZ = Math.max(maxZ, pos.getZ());
            }
        }

        return new AABB(minX, minY, minZ, maxX + 1.0, maxY + 1.0, maxZ + 1.0).inflate(padding);
    }

    private void applyLocalRadiation(ServerLevel serverLevel) {
        AABB box = radiationZone();
        List<LivingEntity> victims = serverLevel.getEntitiesOfClass(LivingEntity.class, box,
                entity -> entity.isAlive() && (!(entity instanceof Player player) || !player.isCreative()));

        int duration = Math.max(40, pulseInterval() * 3);
        // Scale amplifier lightly with charge so a hot crater bites harder.
        int amp = radiationIntensity >= 400 ? 1 : 0;
        BlockPos center = BlockPos.containing(box.getCenter());

        for (LivingEntity entity : victims) {
            // Full GTCEu hazmat / PPE (same as radioactiveHazard ANY trigger) blocks local debuffs.
            if (HazardProperty.HazardTrigger.ANY.protectionType().isProtected(entity)) {
                continue;
            }
            entity.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, duration, amp, true, true, true));
            entity.addEffect(new MobEffectInstance(MobEffects.HUNGER, duration, amp, true, true, true));
            double distSq = entity.distanceToSqr(center.getX() + 0.5, center.getY() + 0.5, center.getZ() + 0.5);
            // Inner half of the zone (includes the multiblock itself).
            if (distSq < (box.getXsize() * box.getZsize()) * 0.15) {
                entity.addEffect(new MobEffectInstance(MobEffects.POISON, duration / 2, 0, true, true, true));
            }
        }
    }

    private void spawnRadiationParticles(ServerLevel serverLevel) {
        // Do NOT use large Gaussian dx/dy/dz from center — that leaks particles past the +7 zone.
        // Spawn each particle at a uniform point inside the radiation AABB (tiny local jitter only).
        AABB box = radiationZone();
        AABB core = structureBounds(0);
        var random = serverLevel.getRandom();

        float t = Math.min(1.0f, radiationIntensity / 250.0f);
        // ~1.5× denser haze at all charge levels vs previous defaults.
        int count = Math.min(180, Math.round((20 + t * 70 + radiationIntensity * 0.08f) * 1.5f));
        int coreCount = Math.min(60, Math.round((8 + t * 28) * 1.5f));
        double speed = 0.01 + t * 0.03;

        spawnParticlesInBox(serverLevel, box, count, speed, random);
        spawnParticlesInBox(serverLevel, core, coreCount, speed * 1.2, random);
    }

    private static void spawnParticlesInBox(ServerLevel level, AABB box, int count, double speed,
                                            RandomSource random) {
        // Inset slightly so jitter (0.15) cannot push particles outside the zone.
        double inset = 0.2;
        double minX = box.minX + inset;
        double maxX = box.maxX - inset;
        double minY = box.minY + inset;
        double maxY = box.maxY - inset;
        double minZ = box.minZ + inset;
        double maxZ = box.maxZ - inset;
        if (minX >= maxX || minY >= maxY || minZ >= maxZ) {
            return;
        }

        for (int i = 0; i < count; i++) {
            double x = minX + random.nextDouble() * (maxX - minX);
            double y = minY + random.nextDouble() * (maxY - minY);
            double z = minZ + random.nextDouble() * (maxZ - minZ);
            level.sendParticles(RAD_PARTICLE, x, y, z, 1, 0.08, 0.08, 0.08, speed);
        }
    }

    @Override
    public void addDisplayText(List<Component> textList) {
        super.addDisplayText(textList);
        if (!isFormed()) {
            return;
        }
        if (radiationIntensity > 0.5f || isActive()) {
            textList.add(Component.translatable(
                    "skufaddon.multiblock.chelyabinsk_proval.hazard_level",
                    Math.round(radiationIntensity)));
            textList.add(Component.translatable(
                    "skufaddon.multiblock.chelyabinsk_proval.hazard_radius",
                    radiationPadding()));
        }
    }
}
