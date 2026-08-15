package com.arturgpt.skufaddon.common.machine.singleblock.tilt;

import com.arturgpt.skufaddon.api.machine.ISaunaProvider;
import com.arturgpt.skufaddon.api.machine.ISaunaReceiver;
import com.arturgpt.skufaddon.common.config.SkufBalanceConfig;

import com.gregtechceu.gtceu.api.GTValues;
import com.gregtechceu.gtceu.api.machine.MetaMachine;
import com.gregtechceu.gtceu.api.machine.TickableSubscription;
import com.gregtechceu.gtceu.api.machine.WorkableTieredMachine;
import com.gregtechceu.gtceu.api.machine.feature.IRecipeLogicMachine;
import com.gregtechceu.gtceu.api.machine.feature.ITieredMachine;
import com.gregtechceu.gtceu.api.machine.trait.RecipeLogic;
import com.gregtechceu.gtceu.api.recipe.ActionResult;
import com.gregtechceu.gtceu.api.recipe.GTRecipe;
import com.gregtechceu.gtceu.api.recipe.RecipeHelper;

import com.lowdragmc.lowdraglib.syncdata.ISubscription;
import com.lowdragmc.lowdraglib.syncdata.annotation.DescSynced;
import com.lowdragmc.lowdraglib.syncdata.annotation.Persisted;
import com.lowdragmc.lowdraglib.syncdata.field.ManagedFieldHolder;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;

import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;

public class SkufTiltRecipeLogic extends RecipeLogic {

    public static final ManagedFieldHolder MANAGED_FIELD_HOLDER = new ManagedFieldHolder(
            SkufTiltRecipeLogic.class, RecipeLogic.MANAGED_FIELD_HOLDER);

    @Persisted
    @DescSynced
    private int tiltLevel = 0;

    @Persisted
    @DescSynced
    private int ticksAtMaxTilt = 0;

    @Persisted
    @DescSynced
    private int hiddenTilt = 0;

    @Persisted
    private int hiddenStallTicks = 0;

    @Persisted
    private int lastHiddenJamOrdinal = HiddenTiltJam.NONE.ordinal();

    @Persisted
    private boolean hiddenPausePenaltyApplied;

    @Persisted
    private boolean hiddenCableDischarged;

    @Persisted
    private boolean hiddenGearDischarged;

    @Nullable
    private ActionResult lastTickFail;

    @Nullable
    private Component lastWaitingReason;

    @Nullable
    private ISubscription energySubs;

    @Nullable
    private TickableSubscription tiltSubscription;

    @Nullable
    private GTRecipe cachedScaledRecipe;

    @Nullable
    private GTRecipe cachedSourceRecipe;

    private int cachedTiltLevel = -1;

    public SkufTiltRecipeLogic(IRecipeLogicMachine machine) {
        super(machine);
    }

    @Override
    public ManagedFieldHolder getFieldHolder() {
        return MANAGED_FIELD_HOLDER;
    }

    @Override
    public void onMachineLoad() {
        super.onMachineLoad();
        if (!getMachine().isRemote() && getMachine() instanceof WorkableTieredMachine workable) {
            energySubs = workable.energyContainer.addChangedListener(this::onEnergyChanged);
        }
        updateTiltTickSubscription();
    }

    @Override
    public void onMachineUnLoad() {
        if (energySubs != null) {
            energySubs.unsubscribe();
            energySubs = null;
        }
        if (tiltSubscription != null) {
            tiltSubscription.unsubscribe();
            tiltSubscription = null;
        }
        invalidateTiltRecipeCache();
        super.onMachineUnLoad();
    }

    @Override
    public void updateTickSubscription() {
        super.updateTickSubscription();
        updateTiltTickSubscription();
    }

    @Override
    public void setWorkingEnabled(boolean isWorkingAllowed) {
        super.setWorkingEnabled(isWorkingAllowed);
        if (isWorkingAllowed) {
            clearEnergyWaitBackoff();
        }
        updateTiltTickSubscription();
    }

    private void onEnergyChanged() {
        if (!isWaiting() || lastRecipe == null) {
            return;
        }
        if (!(getMachine() instanceof WorkableTieredMachine workable)) {
            return;
        }

        GTRecipe scaled = getTiltScaledRecipe(lastRecipe);
        if (scaled == null) {
            return;
        }

        long needed = RecipeHelper.getRealEUt(scaled).getTotalEU();
        if (workable.energyContainer.getEnergyStored() >= needed) {
            clearEnergyWaitBackoff();
            updateTickSubscription();
        }
    }

    private void clearEnergyWaitBackoff() {
        runAttempt = 0;
        runDelay = 0;
    }

    private void updateTiltTickSubscription() {
        if (getMachine().isRemote()) {
            return;
        }
        boolean needsTicks = SkufTiltUtils.needsTiltTicks(tiltLevel, isWorking(), isWorkingEnabled(), isWaiting()) ||
                (tiltLevel > 0 && isInActiveSauna()) ||
                isHiddenJamActive() ||
                hiddenTilt > 0;
        if (needsTicks) {
            tiltSubscription = getMachine().subscribeServerTick(tiltSubscription, this::tiltServerTick);
        } else if (tiltSubscription != null) {
            tiltSubscription.unsubscribe();
            tiltSubscription = null;
        }
    }

    private void tiltServerTick() {
        MetaMachine metaMachine = getMachine();
        int previousTiltLevel = tiltLevel;
        int growInterval = SkufTiltUtils.getTiltGrowInterval();
        int maxTilt = SkufTiltUtils.getMaxTiltLevel();

        if (isInActiveSauna()) {
            // An active sauna relaxes the machine: tilt cools down even while working.
            if (tiltLevel > 0 && metaMachine.getOffsetTimer() % growInterval == 0) {
                tiltLevel--;
            }
            ticksAtMaxTilt = 0;
        } else if (SkufTiltUtils.shouldGrowTilt(isWorking(), isWorkingEnabled())) {
            if (tiltLevel < maxTilt) {
                if (metaMachine.getOffsetTimer() % growInterval == 0) {
                    tiltLevel++;
                }
            } else {
                ticksAtMaxTilt++;
            }
        } else if (SkufTiltUtils.shouldDecayTilt(tiltLevel, isWorking(), isWaiting())) {
            if (metaMachine.getOffsetTimer() % growInterval == 0) {
                tiltLevel--;
            }
            ticksAtMaxTilt = 0;
        }

        if (tiltLevel != previousTiltLevel) {
            invalidateTiltRecipeCache();
        }
        tickHiddenTilt();
        updateTiltTickSubscription();
    }

    @Override
    public void setWaiting(@Nullable Component reason) {
        super.setWaiting(reason);
        lastWaitingReason = reason;
    }

    @Override
    public ActionResult handleTickRecipe(GTRecipe recipe) {
        GTRecipe scaled = getTiltScaledRecipe(recipe);
        ActionResult result = super.handleTickRecipe(scaled != null ? scaled : recipe);
        lastTickFail = result.isSuccess() ? null : result;
        return result;
    }

    private void tickHiddenTilt() {
        // While crafting, ignore stale failureReasons left over from the previous jam.
        if (isWorking()) {
            clearHiddenJamTracking();
            decayHiddenTiltIfDue();
            checkHiddenDischarge();
            return;
        }

        HiddenTiltJam jam = currentHiddenJam();
        if (jam != HiddenTiltJam.NONE || isHiddenJamActive()) {
            HiddenTiltJam previous = HiddenTiltJam.values()[Math.min(lastHiddenJamOrdinal,
                    HiddenTiltJam.values().length - 1)];
            if (jam != HiddenTiltJam.NONE && jam != previous) {
                addHiddenTilt(jam.burstAmount());
                if (tiltLevel >= 61) {
                    addHiddenTilt(SkufBalanceConfig.HIDDEN_TILT_DENIAL_WHILE_WAITING != null ?
                            SkufBalanceConfig.HIDDEN_TILT_DENIAL_WHILE_WAITING.get() : 4);
                }
                lastHiddenJamOrdinal = jam.ordinal();
            }

            if (!isWorkingEnabled() && !hiddenPausePenaltyApplied) {
                addHiddenTilt(SkufBalanceConfig.HIDDEN_TILT_PAUSED_WHILE_JAMMED != null ?
                        SkufBalanceConfig.HIDDEN_TILT_PAUSED_WHILE_JAMMED.get() : 8);
                hiddenPausePenaltyApplied = true;
            }

            hiddenStallTicks++;
            int stallPerDrip = SkufBalanceConfig.HIDDEN_TILT_STALL_PER_SECOND != null ?
                    SkufBalanceConfig.HIDDEN_TILT_STALL_PER_SECOND.get() : 1;
            int stallInterval = SkufBalanceConfig.HIDDEN_TILT_STALL_INTERVAL_TICKS != null ?
                    SkufBalanceConfig.HIDDEN_TILT_STALL_INTERVAL_TICKS.get() : 40;
            if (stallPerDrip > 0 && hiddenStallTicks % Math.max(1, stallInterval) == 0) {
                addHiddenTilt(stallPerDrip);
            }
        } else {
            clearHiddenJamTracking();
            decayHiddenTiltIfDue();
        }

        checkHiddenDischarge();
    }

    private void clearHiddenJamTracking() {
        lastHiddenJamOrdinal = HiddenTiltJam.NONE.ordinal();
        hiddenStallTicks = 0;
        hiddenPausePenaltyApplied = false;
        lastWaitingReason = null;
        lastTickFail = null;
    }

    private void decayHiddenTiltIfDue() {
        if (hiddenTilt <= 0) {
            return;
        }
        int decayInterval = SkufBalanceConfig.HIDDEN_TILT_DECAY_INTERVAL_TICKS != null ?
                SkufBalanceConfig.HIDDEN_TILT_DECAY_INTERVAL_TICKS.get() : 40;
        if (getMachine().getOffsetTimer() % Math.max(1, decayInterval) == 0) {
            hiddenTilt--;
        }
    }

    private void checkHiddenDischarge() {
        int cableAt = SkufBalanceConfig.HIDDEN_TILT_CABLE_BURN_THRESHOLD != null ?
                SkufBalanceConfig.HIDDEN_TILT_CABLE_BURN_THRESHOLD.get() : 60;
        int explodeAt = SkufBalanceConfig.HIDDEN_TILT_GEAR_EXPLODE_THRESHOLD != null ?
                SkufBalanceConfig.HIDDEN_TILT_GEAR_EXPLODE_THRESHOLD.get() : 90;
        if (hiddenTilt < cableAt) {
            hiddenCableDischarged = false;
        }
        if (hiddenTilt < explodeAt) {
            hiddenGearDischarged = false;
        }
        if (hiddenTilt >= cableAt && !hiddenCableDischarged) {
            HiddenTiltDischarge.burnAttachedCables(getMachine());
            hiddenCableDischarged = true;
        }
        if (hiddenTilt >= explodeAt && !hiddenGearDischarged) {
            if (!hiddenCableDischarged) {
                HiddenTiltDischarge.burnAttachedCables(getMachine());
                hiddenCableDischarged = true;
            }
            HiddenTiltDischarge.explodeAttachedEnergyGear(getMachine());
            hiddenGearDischarged = true;
        }
    }

    /** Mid-recipe WAITING or IDLE failureReasons. Not while actively crafting. */
    private boolean isHiddenJamActive() {
        if (isWorking()) {
            return false;
        }
        if (isWaiting()) {
            return true;
        }
        var reasons = getFailureReasons();
        return reasons != null && !reasons.isEmpty();
    }

    private HiddenTiltJam currentHiddenJam() {
        if (isWorking()) {
            return HiddenTiltJam.NONE;
        }
        if (isWaiting()) {
            Component reason = lastWaitingReason != null ? lastWaitingReason : getWaitingReason();
            return HiddenTiltJam.classify(lastTickFail, reason);
        }
        return HiddenTiltJam.classifyFailures(getFailureReasons());
    }

    private void addHiddenTilt(int amount) {
        if (amount <= 0) {
            return;
        }
        int max = SkufBalanceConfig.HIDDEN_TILT_MAX != null ? SkufBalanceConfig.HIDDEN_TILT_MAX.get() : 100;
        hiddenTilt = Math.min(max, hiddenTilt + amount);
    }

    private boolean isInActiveSauna() {
        if (getMachine() instanceof ISaunaReceiver receiver) {
            ISaunaProvider sauna = receiver.getSauna();
            return sauna != null && sauna.isHot();
        }
        return false;
    }

    private void invalidateTiltRecipeCache() {
        cachedScaledRecipe = null;
        cachedSourceRecipe = null;
        cachedTiltLevel = -1;
    }

    public int getTiltLevel() {
        return tiltLevel;
    }

    public int getTicksAtMaxTilt() {
        return ticksAtMaxTilt;
    }

    public int getHiddenTilt() {
        return hiddenTilt;
    }

    private double getTiltMultiplier() {
        return SkufTiltUtils.getTiltMultiplier(tiltLevel);
    }

    @Nullable
    private GTRecipe getTiltScaledRecipe(@Nullable GTRecipe recipe) {
        if (recipe == null || tiltLevel <= 0) {
            return recipe;
        }
        if (recipe == cachedSourceRecipe && tiltLevel == cachedTiltLevel && cachedScaledRecipe != null) {
            return cachedScaledRecipe;
        }
        cachedSourceRecipe = recipe;
        cachedTiltLevel = tiltLevel;
        cachedScaledRecipe = SkufTiltUtils.applyTiltToRecipe(recipe, getTiltMultiplier());
        return cachedScaledRecipe;
    }

    /**
     * Scaled recipe for UI and Jade. Internal tick logic still uses the base {@link #lastRecipe}
     * field and applies tilt scaling in {@link #handleTickRecipe(GTRecipe)}.
     */
    @Override
    @Nullable
    public GTRecipe getLastRecipe() {
        return getTiltScaledRecipe(super.getLastRecipe());
    }

    /**
     * GTCEu Jade prefixes IDLE {@code failureReasons} with red "Fail to setup recipe:".
     * Ordinary IO jams between recipes are not setup failures — hide that fancy tooltip
     * and surface the reason via {@link #getTiltStatusTooltip()} instead.
     */
    @Override
    public boolean showFancyTooltip() {
        if (isWaiting()) {
            return super.showFancyTooltip();
        }
        if (HiddenTiltJam.isIoSetupFailure(getFailureReasons())) {
            return false;
        }
        return super.showFancyTooltip();
    }

    /**
     * Status lines for machine GUI / Jade. Keep tilt/jam text off RecipeLogic
     * {@link #getFancyTooltip()} so idle IO jams do not get a false setup-fail header.
     */
    public List<Component> getTiltStatusTooltip() {
        List<Component> tooltip = new ArrayList<>();

        MetaMachine meta = getMachine();
        if (meta instanceof ITieredMachine tiered) {
            int tier = tiered.getTier();
            tooltip.add(Component.translatable(
                    "skufaddon.tooltip.voltage",
                    GTValues.V[tier],
                    GTValues.VNF[tier])
                    .withStyle(ChatFormatting.GRAY));
        }

        tooltip.add(SkufTiltUtils.getModeComponent(tiltLevel, ticksAtMaxTilt));

        if (isWaiting()) {
            Component reason = lastWaitingReason != null ? lastWaitingReason : getWaitingReason();
            if (reason != null && !reason.getString().isEmpty()) {
                tooltip.add(reason.copy().withStyle(ChatFormatting.YELLOW));
            }
        } else if (HiddenTiltJam.isIoSetupFailure(getFailureReasons())) {
            for (Component reason : getFailureReasons()) {
                if (reason != null && !reason.getString().isEmpty()) {
                    tooltip.add(reason.copy().withStyle(ChatFormatting.YELLOW));
                }
            }
        }

        HiddenTiltJam jam = currentHiddenJam();
        tooltip.add(Component.translatable("skufaddon.tilt.hidden_debug", hiddenTilt, jam.debugKey())
                .withStyle(ChatFormatting.DARK_PURPLE));
        return tooltip;
    }
}
