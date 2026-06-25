package com.arturgpt.skufaddon.common.machine.singleblock.tilt;

import com.arturgpt.skufaddon.api.machine.ISaunaProvider;
import com.arturgpt.skufaddon.api.machine.ISaunaReceiver;
import com.arturgpt.skufaddon.client.render.SkufOverheatRenderer;

import com.gregtechceu.gtceu.api.machine.IMachineBlockEntity;
import com.gregtechceu.gtceu.api.machine.SimpleTieredMachine;
import com.gregtechceu.gtceu.api.machine.trait.RecipeLogic;
import com.gregtechceu.gtceu.common.data.machines.GTMachineUtils;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;

import lombok.Getter;
import org.jetbrains.annotations.Nullable;

public class SkufTiltMachine extends SimpleTieredMachine implements ISaunaReceiver {

    /** How quickly the glow follows a rising target (1 = instant, target itself ramps slowly). */
    private static final float GLOW_FADE_IN = 1.0f;
    /** How quickly the glow decays once the machine leaves peak tilt (per client tick). */
    private static final float GLOW_FADE_OUT = 0.04f;

    @Nullable
    private ISaunaProvider saunaProvider;

    /** Client-only, smoothed overheat intensity in {@code [0, 1]} driving the glow and smoke. */
    @Getter
    private float clientGlowIntensity;
    private boolean clientGlowActive;

    public SkufTiltMachine(IMachineBlockEntity holder, int tier) {
        super(holder, tier, GTMachineUtils.defaultTankSizeFunction);
    }

    @Override
    @Nullable
    public ISaunaProvider getSauna() {
        return saunaProvider;
    }

    @Override
    public void setSauna(@Nullable ISaunaProvider provider) {
        this.saunaProvider = provider;
    }

    @Override
    protected RecipeLogic createRecipeLogic(Object... args) {
        return new SkufTiltRecipeLogic(this);
    }

    @Override
    public void clientTick() {
        super.clientTick();
        updateOverheatVisuals();
    }

    @Override
    public void onUnload() {
        super.onUnload();
        if (isRemote() && clientGlowActive) {
            clientGlowActive = false;
            SkufOverheatRenderer.setActive(this, false);
        }
    }

    private void updateOverheatVisuals() {
        float target = 0.0f;
        if (getRecipeLogic() instanceof SkufTiltRecipeLogic logic) {
            target = SkufTiltUtils.getOverheatProgress(logic.getTiltLevel(), logic.getTicksAtMaxTilt());
        }

        float rate = target > clientGlowIntensity ? GLOW_FADE_IN : GLOW_FADE_OUT;
        clientGlowIntensity += (target - clientGlowIntensity) * rate;
        if (clientGlowIntensity < 0.001f) {
            clientGlowIntensity = 0.0f;
        }

        boolean shouldBeActive = clientGlowIntensity > 0.01f;
        if (shouldBeActive != clientGlowActive) {
            clientGlowActive = shouldBeActive;
            SkufOverheatRenderer.setActive(this, shouldBeActive);
        }

        if (shouldBeActive) {
            spawnOverheatParticles(clientGlowIntensity);
        }
    }

    private void spawnOverheatParticles(float intensity) {
        Level level = getLevel();
        if (level == null) {
            return;
        }
        RandomSource random = level.random;

        // Rhythmic "пыхтение": bursts of thick smoke whose frequency grows with heat.
        int puffInterval = Math.max(1, (int) Mth.lerp(intensity, 24.0f, 6.0f));
        if (getOffsetTimer() % puffInterval == 0) {
            int count = 1 + (int) (intensity * 5.0f);
            for (int i = 0; i < count; i++) {
                emitFromRandomFace(level, random, ParticleTypes.LARGE_SMOKE, intensity);
            }
        }

        // Steady wisps of smoke drifting off every side.
        if (random.nextFloat() < intensity * 0.8f) {
            emitFromRandomFace(level, random, ParticleTypes.SMOKE, intensity);
        }

        // Glowing embers once it is properly overheating.
        if (intensity > 0.6f && random.nextFloat() < (intensity - 0.6f)) {
            emitFromRandomFace(level, random, ParticleTypes.FLAME, intensity);
        }
    }

    private void emitFromRandomFace(Level level, RandomSource random, SimpleParticleType particle, float intensity) {
        BlockPos pos = getPos();
        double x = pos.getX();
        double y = pos.getY();
        double z = pos.getZ();

        double px = x + random.nextDouble();
        double py = y + random.nextDouble();
        double pz = z + random.nextDouble();
        double vx = 0.0;
        double vy = 0.0;
        double vz = 0.0;
        double out = 0.02 + intensity * 0.03;

        // Pin the spawn point to one of the six faces and push the particle outward from it.
        switch (random.nextInt(6)) {
            case 0 -> {
                py = y - 0.05;
                vy = -out * 0.4;
            }            // bottom
            case 1 -> {
                py = y + 1.05;
                vy = out + 0.03;
            }            // top
            case 2 -> {
                pz = z - 0.05;
                vz = -out;
            }                  // north
            case 3 -> {
                pz = z + 1.05;
                vz = out;
            }                   // south
            case 4 -> {
                px = x - 0.05;
                vx = -out;
            }                  // west
            default -> {
                px = x + 1.05;
                vx = out;
            }                  // east
        }

        // Smoke always drifts upward a little regardless of the face it leaves from.
        vy += 0.01 + random.nextDouble() * 0.02;

        level.addParticle(particle, px, py, pz, vx, vy, vz);
    }
}
