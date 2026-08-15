package com.arturgpt.skufaddon.common.machine.singleblock.tilt;

import com.arturgpt.skufaddon.common.config.SkufBalanceConfig;

import com.gregtechceu.gtceu.api.capability.recipe.EURecipeCapability;
import com.gregtechceu.gtceu.api.capability.recipe.IO;
import com.gregtechceu.gtceu.api.recipe.ActionResult;

import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.contents.TranslatableContents;

import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * Why hidden UT is rising. "Wrong item in bus" from the §19.2 table is
 * intentionally omitted — GTCEu does not expose that as a distinct wait reason.
 * <p>
 * GTCEu splits jams into {@code WAITING} (mid-recipe) and IDLE {@code failureReasons}
 * (cannot start next recipe). Both must feed hidden UT.
 */
public enum HiddenTiltJam {

    NONE,
    MISSING_INPUT,
    OUTPUT_FULL,
    NO_ENERGY,
    CONDITION;

    public int burstAmount() {
        return switch (this) {
            case MISSING_INPUT, CONDITION -> SkufBalanceConfig.HIDDEN_TILT_MISSING_INPUT != null ?
                    SkufBalanceConfig.HIDDEN_TILT_MISSING_INPUT.get() : 5;
            case OUTPUT_FULL -> SkufBalanceConfig.HIDDEN_TILT_OUTPUT_FULL != null ?
                    SkufBalanceConfig.HIDDEN_TILT_OUTPUT_FULL.get() : 15;
            case NO_ENERGY -> SkufBalanceConfig.HIDDEN_TILT_NO_ENERGY != null ?
                    SkufBalanceConfig.HIDDEN_TILT_NO_ENERGY.get() : 3;
            case NONE -> 0;
        };
    }

    public String debugKey() {
        return switch (this) {
            case NONE -> "idle";
            case MISSING_INPUT -> "missing_input";
            case OUTPUT_FULL -> "output_full";
            case NO_ENERGY -> "no_energy";
            case CONDITION -> "condition";
        };
    }

    public static HiddenTiltJam classify(@Nullable ActionResult fail, @Nullable Component waitingReason) {
        if (fail != null && !fail.isSuccess()) {
            if (fail.capability() == EURecipeCapability.CAP && fail.io() == IO.IN) {
                return NO_ENERGY;
            }
            if (fail.io() == IO.OUT) {
                return OUTPUT_FULL;
            }
            if (fail.io() == IO.IN) {
                return MISSING_INPUT;
            }
        }
        return fromReason(waitingReason);
    }

    public static HiddenTiltJam classifyFailures(@Nullable List<Component> failureReasons) {
        if (failureReasons == null || failureReasons.isEmpty()) {
            return NONE;
        }
        HiddenTiltJam best = NONE;
        for (Component reason : failureReasons) {
            HiddenTiltJam jam = fromReason(reason);
            if (jam == OUTPUT_FULL) {
                return OUTPUT_FULL;
            }
            if (jam != NONE && best == NONE) {
                best = jam;
            } else if (jam == NO_ENERGY) {
                best = NO_ENERGY;
            } else if (jam == MISSING_INPUT && best != NO_ENERGY) {
                best = MISSING_INPUT;
            } else if (jam == CONDITION && best == NONE) {
                best = CONDITION;
            }
        }
        return best;
    }

    /** True when Jade would otherwise label a normal IO jam as "Fail to setup recipe". */
    public static boolean isIoSetupFailure(@Nullable List<Component> failureReasons) {
        HiddenTiltJam jam = classifyFailures(failureReasons);
        return jam == MISSING_INPUT || jam == OUTPUT_FULL || jam == NO_ENERGY;
    }

    private static HiddenTiltJam fromReason(@Nullable Component reason) {
        String key = translationKey(reason);
        if (key == null) {
            return NONE;
        }
        if (key.contains("insufficient_out")) {
            return OUTPUT_FULL;
        }
        if (key.contains("insufficient_in")) {
            // Jade reason is often "Недостаточно ввода: EU" for power — check siblings via text
            if (key.contains("eu") || looksLikeEnergy(reason)) {
                return NO_ENERGY;
            }
            return MISSING_INPUT;
        }
        if (key.contains("condition_fails")) {
            return CONDITION;
        }
        // Nested appendages: "insufficient_in: Fluid" etc. already matched by contains above.
        String plain = reason.getString();
        if (plain != null) {
            String lower = plain.toLowerCase();
            if (lower.contains("eu") && (lower.contains("недостаточно") || lower.contains("insufficient"))) {
                return NO_ENERGY;
            }
        }
        return NONE;
    }

    private static boolean looksLikeEnergy(@Nullable Component reason) {
        if (reason == null) {
            return false;
        }
        for (Component sibling : reason.getSiblings()) {
            String key = translationKey(sibling);
            if (key != null && (key.contains("eu") || key.contains("energy") || key.contains("electric"))) {
                return true;
            }
            String text = sibling.getString();
            if (text != null && text.toUpperCase().contains("EU")) {
                return true;
            }
        }
        return false;
    }

    @Nullable
    private static String translationKey(@Nullable Component reason) {
        if (reason == null) {
            return null;
        }
        if (reason.getContents() instanceof TranslatableContents translatable) {
            return translatable.getKey();
        }
        for (Component sibling : reason.getSiblings()) {
            if (sibling.getContents() instanceof TranslatableContents translatable) {
                return translatable.getKey();
            }
        }
        return reason.getString();
    }
}
