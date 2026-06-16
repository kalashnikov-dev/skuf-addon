package com.arturgpt.skufaddon.common.machine.tilt;

import com.gregtechceu.gtceu.api.capability.recipe.EURecipeCapability;
import com.gregtechceu.gtceu.api.recipe.GTRecipe;
import com.gregtechceu.gtceu.api.recipe.RecipeHelper;
import com.gregtechceu.gtceu.api.recipe.ingredient.EnergyStack;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;

import org.jetbrains.annotations.Nullable;

public final class SkufTiltUtils {

    private SkufTiltUtils() {}

    public static final int TILT_GROW_INTERVAL = 40;
    public static final int MAX_TILT_LEVEL = 100;
    /** Ticks at max tilt before the level is hidden in tooltips (1 second). */
    public static final int HIDDEN_MODE_DELAY_TICKS = 20;

    public static double getTiltMultiplier(int tiltLevel) {
        return 1.0 + (tiltLevel / (double) MAX_TILT_LEVEL) * 3.0;
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
        if (tiltLevel >= MAX_TILT_LEVEL && ticksAtMaxTilt >= HIDDEN_MODE_DELAY_TICKS) {
            return Component.translatable("skufaddon.tilt.mode.hidden")
                    .withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD);
        }
        if (tiltLevel >= MAX_TILT_LEVEL) {
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
