package com.arturgpt.skufaddon.common.machine.multiblock.sauna;

import com.arturgpt.skufaddon.common.data.SkufMaterials;

import com.gregtechceu.gtceu.api.GTValues;
import com.gregtechceu.gtceu.api.capability.IEnergyContainer;
import com.gregtechceu.gtceu.api.capability.IWorkable;
import com.gregtechceu.gtceu.api.capability.recipe.EURecipeCapability;
import com.gregtechceu.gtceu.api.machine.feature.multiblock.IMaintenanceMachine;
import com.gregtechceu.gtceu.api.machine.trait.RecipeLogic;
import com.gregtechceu.gtceu.api.transfer.fluid.FluidHandlerList;
import com.gregtechceu.gtceu.utils.GTTransferUtils;

import com.lowdragmc.lowdraglib.syncdata.annotation.Persisted;
import com.lowdragmc.lowdraglib.syncdata.field.ManagedFieldHolder;

import net.minecraft.network.chat.Component;
import net.minecraft.util.Mth;
import net.minecraftforge.fluids.FluidStack;
import net.minecraftforge.fluids.capability.IFluidHandler.FluidAction;

import org.jetbrains.annotations.Nullable;

/**
 * Drives the Sauna Egora multiblock. Closely mirrors GregTech's {@code CleanroomLogic}, but
 * accumulates "heat" instead of "cleanliness". While hot, the sauna also condenses diluted sweat
 * into its fluid output hatch.
 */
public class SaunaEgoraLogic extends RecipeLogic implements IWorkable {

    public static final int BASE_HEAT_AMOUNT = 2;
    public static final int HEAT_AMOUNT_THRESHOLD = 95;
    public static final int FLUID_PRODUCTION_INTERVAL = 20;

    protected static final ManagedFieldHolder MANAGED_FIELD_HOLDER = new ManagedFieldHolder(
            SaunaEgoraLogic.class, RecipeLogic.MANAGED_FIELD_HOLDER);

    @Nullable
    private IMaintenanceMachine maintenanceMachine;

    @Nullable
    private IEnergyContainer energyContainer;

    @Nullable
    private FluidHandlerList outputFluidHandler;

    @Persisted
    private int heatAmount;

    public SaunaEgoraLogic(SaunaEgoraMachine machine) {
        super(machine);
    }

    @Override
    public SaunaEgoraMachine getMachine() {
        return (SaunaEgoraMachine) machine;
    }

    @Override
    public ManagedFieldHolder getFieldHolder() {
        return MANAGED_FIELD_HOLDER;
    }

    public int getHeatAmount() {
        return heatAmount;
    }

    public void adjustHeatAmount(int amount) {
        this.heatAmount = Mth.clamp(this.heatAmount + amount, 0, 100);
    }

    public void resetHeatAmount() {
        this.heatAmount = 0;
    }

    public void setDuration(int duration) {
        this.duration = duration;
    }

    @Override
    public void serverTick() {
        if (duration <= 0) {
            return;
        }

        // The sauna must be powered by at least an EV energy hatch.
        if (getMachine().getTier() < GTValues.EV) {
            setWaiting(Component.translatable("skufaddon.multiblock.sauna_egora.insufficient_tier"));
            return;
        }

        if (maintenanceMachine == null || maintenanceMachine.getNumMaintenanceProblems() < 6) {
            if (!consumeEnergy()) {
                if (progress > 0 && machine.regressWhenWaiting()) {
                    this.progress = 1;
                }
                if (machine.self().getOffsetTimer() % duration == 0) {
                    adjustHeat(true);
                }
                setWaiting(Component.translatable("gtceu.recipe_logic.insufficient_in").append(": ")
                        .append(EURecipeCapability.CAP.getName()));
                return;
            }
            setStatus(Status.WORKING);
            if (getMachine().isHot()) {
                tryProduceDilutedSweat();
            }
            if (progress++ < getMaxProgress()) {
                if (!machine.onWorking()) {
                    this.interruptRecipe();
                }
                return;
            }
            progress = 0;
            if (!machine.beforeWorking(null)) {
                return;
            }
            adjustHeat(false);
        } else {
            if (progress > 0) {
                progress--;
            }
            if (machine.self().getOffsetTimer() % duration == 0) {
                adjustHeat(true);
            }
            setStatus(Status.IDLE);
            machine.afterWorking();
        }
    }

    private void tryProduceDilutedSweat() {
        if (outputFluidHandler == null) {
            return;
        }
        if (machine.self().getOffsetTimer() % FLUID_PRODUCTION_INTERVAL != 0) {
            return;
        }

        int amount = getMachine().getDilutedSweatAmountPerCycle();
        FluidStack stack = SkufMaterials.dilutedSweat.getFluid(amount);
        int filled = GTTransferUtils.fillFluidAccountNotifiableList(outputFluidHandler, stack, FluidAction.EXECUTE);
        if (filled <= 0) {
            setWaiting(Component.translatable("skufaddon.multiblock.sauna_egora.sweat_output_full"));
        }
    }

    private void adjustHeat(boolean declined) {
        int amount = BASE_HEAT_AMOUNT + (3 * (getTierDifference() + 1));
        if (declined) {
            amount *= -1;
        }
        if (maintenanceMachine != null) {
            amount -= maintenanceMachine.getNumMaintenanceProblems();
        }
        getMachine().applyHeatDelta(amount);
    }

    private boolean consumeEnergy() {
        int tier = Mth.clamp(getMachine().getTier(), GTValues.ULV, GTValues.MAX);
        long energyToDrain = getMachine().isHot() ? Math.max(8L, 3L * GTValues.V[tier] / 16L) : GTValues.VA[tier];
        if (energyContainer != null) {
            long resultEnergy = energyContainer.getEnergyStored() - energyToDrain;
            if (resultEnergy >= 0L && resultEnergy <= energyContainer.getEnergyCapacity()) {
                energyContainer.removeEnergy(energyToDrain);
                return true;
            }
        }
        return false;
    }

    private int getTierDifference() {
        return Math.max(0, getMachine().getTier() - GTValues.EV);
    }

    public void setMaintenanceMachine(@Nullable IMaintenanceMachine maintenanceMachine) {
        this.maintenanceMachine = maintenanceMachine;
    }

    public void setEnergyContainer(@Nullable IEnergyContainer energyContainer) {
        this.energyContainer = energyContainer;
    }

    public void setOutputFluidHandler(@Nullable FluidHandlerList outputFluidHandler) {
        this.outputFluidHandler = outputFluidHandler;
    }
}
