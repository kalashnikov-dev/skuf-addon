package com.arturgpt.skufaddon.common.machine.singleblock.tilt;

import com.arturgpt.skufaddon.common.config.SkufBalanceConfig;

import com.gregtechceu.gtceu.api.capability.recipe.EURecipeCapability;
import com.gregtechceu.gtceu.api.recipe.GTRecipe;
import com.gregtechceu.gtceu.api.recipe.RecipeHelper;
import com.gregtechceu.gtceu.api.recipe.ingredient.EnergyStack;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;

import org.jetbrains.annotations.Nullable;

public final class SkufTiltUtils {

    private SkufTiltUtils() {}

    public static int getMaxTiltLevel() {
        return SkufBalanceConfig.MAX_TILT_LEVEL != null ? SkufBalanceConfig.MAX_TILT_LEVEL.get() : 100;
    }

    public static int getTiltGrowInterval() {
        return SkufBalanceConfig.TILT_GROW_INTERVAL_TICKS != null ? SkufBalanceConfig.TILT_GROW_INTERVAL_TICKS.get() :
                40;
    }

    public static double getTiltMultiplierMax() {
        return SkufBalanceConfig.TILT_MULTIPLIER_MAX != null ? SkufBalanceConfig.TILT_MULTIPLIER_MAX.get() : 4.0;
    }

    public static int getOverheatRampTicks() {
        return SkufBalanceConfig.OVERHEAT_RAMP_TICKS != null ? SkufBalanceConfig.OVERHEAT_RAMP_TICKS.get() : 600;
    }

    public static int getHiddenModeDelayTicks() {
        return SkufBalanceConfig.HIDDEN_MODE_DELAY_TICKS != null ? SkufBalanceConfig.HIDDEN_MODE_DELAY_TICKS.get() : 20;
    }

    public static final int TILT_GROW_INTERVAL = 40;
    public static final int MAX_TILT_LEVEL = 100;
    public static final int HIDDEN_MODE_DELAY_TICKS = 20;
    public static final int OVERHEAT_RAMP_TICKS = 600;

    /**
     * Visual overheat progress in {@code [0, 1]}. Non-zero only once the machine is at peak tilt,
     * then ramps up the longer it stays there. Used client-side to drive the red glow and smoke.
     */
    public static float getOverheatProgress(int tiltLevel, int ticksAtMaxTilt) {
        int maxLevel = getMaxTiltLevel();
        if (tiltLevel < maxLevel) {
            return 0.0f;
        }
        float progress = ticksAtMaxTilt / (float) getOverheatRampTicks();
        if (progress < 0.0f) {
            return 0.0f;
        }
        return Math.min(progress, 1.0f);
    }

    public static double getTiltMultiplier(int tiltLevel) {
        double maxMult = getTiltMultiplierMax();
        return 1.0 + (tiltLevel / (double) getMaxTiltLevel()) * (maxMult - 1.0);
    }

    /**
     * Scales EU/t by raising amperage (hull input limit) and fine-tuning voltage so
     * {@code voltage * amperage} tracks the target EU/t smoothly instead of jumping in
     * fixed voltage steps.
     */
    @Nullable
    public static GTRecipe applyTiltToRecipe(@Nullable GTRecipe recipe, double multiplier) {
        if (recipe == null || multiplier <= 1.0) {
            return recipe;
        }

        EnergyStack.WithIO preEUt = RecipeHelper.getRealEUtWithIO(recipe);
        if (preEUt.isEmpty()) {
            return recipe;
        }

        long baseVoltage = preEUt.voltage();
        long baseAmperage = preEUt.amperage();
        long targetTotal = Math.max(1L, Math.round(preEUt.getTotalEU() * multiplier));

        long minAmperage = Math.max(1L, (long) Math.floor(baseAmperage * multiplier));
        long maxAmperage = Math.max(minAmperage, (long) Math.ceil(baseAmperage * multiplier));

        long bestVoltage = baseVoltage;
        long bestAmperage = minAmperage;
        long bestError = Long.MAX_VALUE;

        for (long amperage = minAmperage; amperage <= maxAmperage + 1L; amperage++) {
            long voltage = Math.max(1L, (targetTotal + amperage - 1L) / amperage);
            long actualTotal = voltage * amperage;
            long error = Math.abs(actualTotal - targetTotal);
            if (error < bestError) {
                bestError = error;
                bestVoltage = voltage;
                bestAmperage = amperage;
            }
        }

        GTRecipe copied = recipe.copy();
        EnergyStack scaled = new EnergyStack(bestVoltage, bestAmperage);
        EURecipeCapability.putEUContent(
                preEUt.isInput() ? copied.tickInputs : copied.tickOutputs,
                scaled);
        return copied;
    }

    public static Component getModeComponent(int tiltLevel, int ticksAtMaxTilt) {
        int maxLevel = getMaxTiltLevel();
        if (tiltLevel >= maxLevel && ticksAtMaxTilt >= getHiddenModeDelayTicks()) {
            return Component.translatable("skufaddon.tilt.mode.hidden")
                    .withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD);
        }
        if (tiltLevel >= maxLevel) {
            return Component.translatable("skufaddon.tilt.mode.peak", tiltLevel)
                    .withStyle(ChatFormatting.RED);
        }
        if (tiltLevel <= 30) {
            return Component.translatable("skufaddon.tilt.mode.ugor", tiltLevel)
                    .withStyle(ChatFormatting.GREEN);
        }
        if (tiltLevel <= 60) {
            return Component.translatable("skufaddon.tilt.mode.pot", tiltLevel)
                    .withStyle(ChatFormatting.YELLOW);
        }
        return Component.translatable("skufaddon.tilt.mode.no_sweat", tiltLevel)
                .withStyle(ChatFormatting.GOLD);
    }

    public static boolean shouldGrowTilt(boolean isWorking, boolean isWorkingEnabled) {
        return isWorking && isWorkingEnabled;
    }

    public static boolean shouldDecayTilt(int tiltLevel, boolean isWorking, boolean isWaiting) {
        return tiltLevel > 0 && !isWorking && !isWaiting;
    }

    public static boolean needsTiltTicks(int tiltLevel, boolean isWorking, boolean isWorkingEnabled,
                                         boolean isWaiting) {
        return shouldGrowTilt(isWorking, isWorkingEnabled) || shouldDecayTilt(tiltLevel, isWorking, isWaiting);
    }
}
