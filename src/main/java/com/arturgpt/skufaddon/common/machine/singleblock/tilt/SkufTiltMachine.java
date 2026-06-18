package com.arturgpt.skufaddon.common.machine.singleblock.tilt;

import com.arturgpt.skufaddon.api.machine.ISaunaProvider;
import com.arturgpt.skufaddon.api.machine.ISaunaReceiver;

import com.gregtechceu.gtceu.api.machine.IMachineBlockEntity;
import com.gregtechceu.gtceu.api.machine.SimpleTieredMachine;
import com.gregtechceu.gtceu.api.machine.trait.RecipeLogic;
import com.gregtechceu.gtceu.common.data.machines.GTMachineUtils;

import org.jetbrains.annotations.Nullable;

public class SkufTiltMachine extends SimpleTieredMachine implements ISaunaReceiver {

    @Nullable
    private ISaunaProvider saunaProvider;

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
}
