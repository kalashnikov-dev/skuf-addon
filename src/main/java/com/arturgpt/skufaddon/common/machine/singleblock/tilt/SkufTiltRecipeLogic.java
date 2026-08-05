package com.arturgpt.skufaddon.common.machine.singleblock.tilt;

import com.arturgpt.skufaddon.api.machine.ISaunaProvider;
import com.arturgpt.skufaddon.api.machine.ISaunaReceiver;

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
                (tiltLevel > 0 && isInActiveSauna());
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
        updateTiltTickSubscription();
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

    @Override
    public ActionResult handleTickRecipe(GTRecipe recipe) {
        GTRecipe scaled = getTiltScaledRecipe(recipe);
        return super.handleTickRecipe(scaled != null ? scaled : recipe);
    }

    /**
     * Status lines for machine GUI / Jade. Do not put these through
     * {@link #getFancyTooltip()} — GTCEu Jade treats a non-empty RecipeLogic fancy
     * tooltip on an idle machine as {@code gtceu.recipe_logic.setup_fail}.
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
        return tooltip;
    }
}
