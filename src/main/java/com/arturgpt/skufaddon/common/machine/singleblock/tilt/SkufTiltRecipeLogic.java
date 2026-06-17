package com.arturgpt.skufaddon.common.machine.singleblock.tilt;

import com.gregtechceu.gtceu.api.GTValues;
import com.gregtechceu.gtceu.api.gui.GuiTextures;
import com.gregtechceu.gtceu.api.machine.MetaMachine;
import com.gregtechceu.gtceu.api.machine.TickableSubscription;
import com.gregtechceu.gtceu.api.machine.WorkableTieredMachine;
import com.gregtechceu.gtceu.api.machine.feature.IRecipeLogicMachine;
import com.gregtechceu.gtceu.api.machine.feature.ITieredMachine;
import com.gregtechceu.gtceu.api.machine.trait.RecipeLogic;
import com.gregtechceu.gtceu.api.recipe.ActionResult;
import com.gregtechceu.gtceu.api.recipe.GTRecipe;
import com.gregtechceu.gtceu.api.recipe.RecipeHelper;
import com.gregtechceu.gtceu.api.recipe.ingredient.EnergyStack;

import com.lowdragmc.lowdraglib.gui.texture.IGuiTexture;
import com.lowdragmc.lowdraglib.syncdata.ISubscription;
import com.lowdragmc.lowdraglib.syncdata.annotation.DescSynced;
import com.lowdragmc.lowdraglib.syncdata.annotation.Persisted;
import com.lowdragmc.lowdraglib.syncdata.field.ManagedFieldHolder;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;

import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

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
        if (SkufTiltUtils.needsTiltTicks(tiltLevel, isWorking(), isWorkingEnabled(), isWaiting())) {
            tiltSubscription = getMachine().subscribeServerTick(tiltSubscription, this::tiltServerTick);
        } else if (tiltSubscription != null) {
            tiltSubscription.unsubscribe();
            tiltSubscription = null;
        }
    }

    private void tiltServerTick() {
        MetaMachine metaMachine = getMachine();
        int previousTiltLevel = tiltLevel;

        if (SkufTiltUtils.shouldGrowTilt(isWorking(), isWorkingEnabled())) {
            if (tiltLevel < SkufTiltUtils.MAX_TILT_LEVEL) {
                if (metaMachine.getOffsetTimer() % SkufTiltUtils.TILT_GROW_INTERVAL == 0) {
                    tiltLevel++;
                }
            } else {
                ticksAtMaxTilt++;
            }
        } else if (SkufTiltUtils.shouldDecayTilt(tiltLevel, isWorking(), isWaiting())) {
            if (metaMachine.getOffsetTimer() % SkufTiltUtils.TILT_GROW_INTERVAL == 0) {
                tiltLevel--;
            }
            ticksAtMaxTilt = 0;
        }

        if (tiltLevel != previousTiltLevel) {
            invalidateTiltRecipeCache();
        }
        updateTiltTickSubscription();
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

    @Override
    public IGuiTexture getFancyTooltipIcon() {
        return GuiTextures.INFO_ICON;
    }

    @Override
    public boolean showFancyTooltip() {
        return true;
    }

    @Override
    public List<Component> getFancyTooltip() {
        List<Component> tooltip = new ArrayList<>();
        List<Component> original = super.getFancyTooltip();
        if (original != null) {
            tooltip.addAll(original);
        }

        GTRecipe displayRecipe = getLastRecipe();
        if (displayRecipe != null) {
            EnergyStack energy = RecipeHelper.getRealEUt(displayRecipe);
            long effectiveEUt = energy.getTotalEU();
            String amperage = formatAmperage(energy.amperage());
            if (tiltLevel > 0) {
                tooltip.add(Component.translatable(
                        "skufaddon.tooltip.eut_with_tilt",
                        amperage,
                        effectiveEUt,
                        String.format(Locale.ROOT, "%.2f", getTiltMultiplier()))
                        .withStyle(ChatFormatting.AQUA));
            } else {
                tooltip.add(Component.translatable(
                        "skufaddon.tooltip.eut",
                        amperage,
                        effectiveEUt)
                        .withStyle(ChatFormatting.GRAY));
            }
        }

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

    private static String formatAmperage(long amperage) {
        return String.format(Locale.ROOT, "%.2f", (double) amperage);
    }
}
