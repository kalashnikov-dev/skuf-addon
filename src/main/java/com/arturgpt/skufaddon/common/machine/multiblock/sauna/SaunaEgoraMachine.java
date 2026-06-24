package com.arturgpt.skufaddon.common.machine.multiblock.sauna;

import com.arturgpt.skufaddon.api.machine.ISaunaProvider;
import com.arturgpt.skufaddon.api.machine.ISaunaReceiver;

import com.gregtechceu.gtceu.api.GTValues;
import com.gregtechceu.gtceu.api.capability.IEnergyContainer;
import com.gregtechceu.gtceu.api.capability.recipe.EURecipeCapability;
import com.gregtechceu.gtceu.api.capability.recipe.FluidRecipeCapability;
import com.gregtechceu.gtceu.api.capability.recipe.IO;
import com.gregtechceu.gtceu.api.machine.IMachineBlockEntity;
import com.gregtechceu.gtceu.api.machine.feature.multiblock.IDisplayUIMachine;
import com.gregtechceu.gtceu.api.machine.feature.multiblock.IMaintenanceMachine;
import com.gregtechceu.gtceu.api.machine.feature.multiblock.IMultiPart;
import com.gregtechceu.gtceu.api.machine.multiblock.WorkableElectricMultiblockMachine;
import com.gregtechceu.gtceu.api.machine.multiblock.WorkableMultiblockMachine;
import com.gregtechceu.gtceu.api.machine.trait.RecipeHandlerList;
import com.gregtechceu.gtceu.api.machine.trait.RecipeLogic;
import com.gregtechceu.gtceu.api.misc.EnergyContainerList;
import com.gregtechceu.gtceu.api.transfer.fluid.FluidHandlerList;
import com.gregtechceu.gtceu.common.machine.electric.HullMachine;
import com.gregtechceu.gtceu.common.machine.multiblock.part.DiodePartMachine;
import com.gregtechceu.gtceu.utils.GTUtil;

import com.lowdragmc.lowdraglib.syncdata.field.ManagedFieldHolder;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.Style;
import net.minecraftforge.fluids.capability.IFluidHandler;

import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Sets;
import it.unimi.dsi.fastutil.longs.Long2ObjectMap;
import it.unimi.dsi.fastutil.longs.Long2ObjectMaps;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Set;

/**
 * Controller for the Sauna Egora multiblock. Acts as an {@link ISaunaProvider}: while the structure
 * is hot it relaxes (lowers) the tilt level of any {@link ISaunaReceiver} tilt machines that were
 * found inside its cavity when the structure formed.
 */
public class SaunaEgoraMachine extends WorkableElectricMultiblockMachine implements ISaunaProvider, IDisplayUIMachine {

    /** mB produced per {@link SaunaEgoraLogic#FLUID_PRODUCTION_INTERVAL} while hot. */
    public static final int STEAM_BASE_MB = 80;
    public static final int STEAM_MB_PER_TIER = 40;
    public static final int STEAM_MB_PER_TILT = 60;

    protected static final ManagedFieldHolder MANAGED_FIELD_HOLDER = new ManagedFieldHolder(
            SaunaEgoraMachine.class, WorkableMultiblockMachine.MANAGED_FIELD_HOLDER);

    @Nullable
    private EnergyContainerList inputEnergyContainers;

    @Nullable
    private FluidHandlerList inputFluidHandlers;

    @Nullable
    private FluidHandlerList outputFluidHandlers;

    @Nullable
    private Collection<ISaunaReceiver> saunaReceivers;

    public SaunaEgoraMachine(IMachineBlockEntity holder) {
        super(holder);
    }

    @Override
    public ManagedFieldHolder getFieldHolder() {
        return MANAGED_FIELD_HOLDER;
    }

    @Override
    protected RecipeLogic createRecipeLogic(Object... args) {
        return new SaunaEgoraLogic(this);
    }

    @Override
    public SaunaEgoraLogic getRecipeLogic() {
        return (SaunaEgoraLogic) super.getRecipeLogic();
    }

    @Override
    public void onStructureFormed() {
        super.onStructureFormed();
        initializeAbilities();
        bindReceivers();
        getRecipeLogic().setDuration(400);
    }

    @Override
    public void onStructureInvalid() {
        super.onStructureInvalid();
        this.inputEnergyContainers = null;
        this.inputFluidHandlers = null;
        this.outputFluidHandlers = null;
        getRecipeLogic().resetHeatAmount();
        unbindReceivers();
    }

    private void bindReceivers() {
        if (saunaReceivers != null) {
            saunaReceivers.forEach(receiver -> receiver.setSauna(null));
            saunaReceivers = null;
        }
        Set<ISaunaReceiver> receivers = getMultiblockState().getMatchContext()
                .getOrCreate("saunaReceiver", Sets::newHashSet);
        this.saunaReceivers = ImmutableSet.copyOf(receivers);
        this.saunaReceivers.forEach(receiver -> receiver.setSauna(this));
    }

    private void unbindReceivers() {
        if (saunaReceivers != null) {
            saunaReceivers.forEach(receiver -> receiver.setSauna(null));
            saunaReceivers = null;
        }
    }

    @Override
    public boolean shouldAddPartToController(IMultiPart part) {
        var cache = getMultiblockState().getCache();
        for (Direction side : GTUtil.DIRECTIONS) {
            if (!cache.contains(part.self().getPos().relative(side))) {
                return true;
            }
        }
        return false;
    }

    protected void initializeAbilities() {
        List<IEnergyContainer> energyContainers = new ArrayList<>();
        List<IFluidHandler> fluidInputHandlers = new ArrayList<>();
        List<IFluidHandler> fluidOutputHandlers = new ArrayList<>();
        Long2ObjectMap<IO> ioMap = getMultiblockState().getMatchContext()
                .getOrCreate("ioMap", Long2ObjectMaps::emptyMap);
        for (IMultiPart part : getParts()) {
            if (isPartIgnored(part)) continue;
            IO io = ioMap.getOrDefault(part.self().getPos().asLong(), IO.BOTH);
            if (io != IO.NONE && io != IO.OUT) {
                for (RecipeHandlerList handlerList : part.getRecipeHandlers()) {
                    if (!handlerList.isValid(io)) continue;
                    handlerList.getCapability(EURecipeCapability.CAP).stream()
                            .filter(IEnergyContainer.class::isInstance)
                            .map(IEnergyContainer.class::cast)
                            .forEach(energyContainers::add);
                    handlerList.getCapability(FluidRecipeCapability.CAP).stream()
                            .filter(IFluidHandler.class::isInstance)
                            .map(IFluidHandler.class::cast)
                            .forEach(fluidInputHandlers::add);
                }
            }
            if (io != IO.NONE && io != IO.IN) {
                for (RecipeHandlerList handlerList : part.getRecipeHandlers()) {
                    if (!handlerList.isValid(io)) continue;
                    handlerList.getCapability(FluidRecipeCapability.CAP).stream()
                            .filter(IFluidHandler.class::isInstance)
                            .map(IFluidHandler.class::cast)
                            .forEach(fluidOutputHandlers::add);
                }
            }
            if (part instanceof IMaintenanceMachine maintenanceMachine) {
                getRecipeLogic().setMaintenanceMachine(maintenanceMachine);
            }
        }
        this.inputEnergyContainers = new EnergyContainerList(energyContainers);
        this.inputFluidHandlers = fluidInputHandlers.isEmpty() ? null : new FluidHandlerList(fluidInputHandlers);
        this.outputFluidHandlers = fluidOutputHandlers.isEmpty() ? null : new FluidHandlerList(fluidOutputHandlers);
        getRecipeLogic().setEnergyContainer(this.inputEnergyContainers);
        getRecipeLogic().setInputFluidHandler(this.inputFluidHandlers);
        getRecipeLogic().setOutputFluidHandler(this.outputFluidHandlers);
        this.tier = Math.min(GTValues.MAX, GTUtil.getFloorTierByVoltage(getMaxVoltage()));
    }

    private static boolean isPartIgnored(IMultiPart part) {
        if (part instanceof DiodePartMachine) return true;
        return part instanceof HullMachine;
    }

    public void applyHeatDelta(int amount) {
        getRecipeLogic().adjustHeatAmount(amount);
    }

    @Override
    public boolean isHot() {
        return getRecipeLogic().getHeatAmount() >= SaunaEgoraLogic.HEAT_AMOUNT_THRESHOLD;
    }

    public int getSaunaReceiverCount() {
        return saunaReceivers != null ? saunaReceivers.size() : 0;
    }

    /** mB of warm vibe steam per production cycle while the sauna is hot. */
    public int getWarmVibeSteamAmountPerCycle() {
        int tierBonus = Math.max(0, getTier() - GTValues.EV) * STEAM_MB_PER_TIER;
        int tiltBonus = getSaunaReceiverCount() * STEAM_MB_PER_TILT;
        return STEAM_BASE_MB + tierBonus + tiltBonus;
    }

    /** mB per second at 20-tick production interval. */
    public int getWarmVibeSteamRatePerSecond() {
        return getWarmVibeSteamAmountPerCycle() * 20 / SaunaEgoraLogic.FLUID_PRODUCTION_INTERVAL;
    }

    /** Water consumed per tick while the sauna is running (scales with steam output). */
    public int getWaterAmountPerTick() {
        return Math.max(1, getWarmVibeSteamAmountPerCycle() / SaunaEgoraLogic.FLUID_PRODUCTION_INTERVAL);
    }

    /** mB of water per second at 20-tick production interval. */
    public int getWaterRatePerSecond() {
        return getWaterAmountPerTick() * 20;
    }

    @Override
    public void addDisplayText(List<Component> textList) {
        if (isFormed()) {
            long maxVoltage = getMaxVoltage();
            if (maxVoltage > 0) {
                String voltageName = GTValues.VNF[GTUtil.getFloorTierByVoltage(maxVoltage)];
                textList.add(Component.translatable("gtceu.multiblock.max_energy_per_tick", maxVoltage, voltageName));
            }

            if (!isWorkingEnabled()) {
                textList.add(Component.translatable("gtceu.multiblock.work_paused"));
            } else if (isActive()) {
                textList.add(Component.translatable("gtceu.multiblock.running"));
                int currentProgress = (int) (recipeLogic.getProgressPercent() * 100);
                double maxInSec = recipeLogic.getDuration() / 20.0d;
                double currentInSec = recipeLogic.getProgress() / 20.0d;
                textList.add(Component.translatable("gtceu.multiblock.progress",
                        String.format("%.2f", currentInSec), String.format("%.2f", maxInSec), currentProgress));
            } else {
                textList.add(Component.translatable("gtceu.multiblock.idling"));
            }

            if (recipeLogic.isWaiting()) {
                textList.add(Component.translatable("gtceu.multiblock.waiting").withStyle(ChatFormatting.RED));
            }

            if (isHot()) {
                textList.add(Component.translatable("skufaddon.multiblock.sauna_egora.hot"));
                textList.add(Component.translatable("skufaddon.multiblock.sauna_egora.steam_rate",
                        getWarmVibeSteamRatePerSecond()));
            } else {
                textList.add(Component.translatable("skufaddon.multiblock.sauna_egora.cold"));
            }
            textList.add(Component.translatable("skufaddon.multiblock.sauna_egora.heat_amount",
                    getRecipeLogic().getHeatAmount()));
        } else {
            Component tooltip = Component.translatable("gtceu.multiblock.invalid_structure.tooltip")
                    .withStyle(ChatFormatting.GRAY);
            textList.add(Component.translatable("gtceu.multiblock.invalid_structure")
                    .withStyle(Style.EMPTY.withColor(ChatFormatting.RED)
                            .withHoverEvent(new HoverEvent(HoverEvent.Action.SHOW_TEXT, tooltip))));
        }
    }

    @Override
    public long getMaxVoltage() {
        if (inputEnergyContainers == null) return GTValues.EV;
        return inputEnergyContainers.getInputVoltage();
    }

    @Override
    public boolean keepSubscribing() {
        return true;
    }

    // The sauna is never paused; it runs whenever powered.
    @Override
    public boolean isWorkingEnabled() {
        return true;
    }

    @Override
    public void setWorkingEnabled(boolean ignored) {}

    @Nullable
    public EnergyContainerList getInputEnergyContainers() {
        return inputEnergyContainers;
    }

    @Nullable
    public FluidHandlerList getInputFluidHandlers() {
        return inputFluidHandlers;
    }

    @Nullable
    public FluidHandlerList getOutputFluidHandlers() {
        return outputFluidHandlers;
    }

    @Nullable
    public Collection<ISaunaReceiver> getSaunaReceivers() {
        return saunaReceivers;
    }
}
