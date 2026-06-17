package com.arturgpt.skufaddon.common.machine.singleblock.tilt;

import com.gregtechceu.gtceu.api.machine.IMachineBlockEntity;
import com.gregtechceu.gtceu.api.machine.SimpleTieredMachine;
import com.gregtechceu.gtceu.api.machine.trait.RecipeLogic;
import com.gregtechceu.gtceu.common.data.machines.GTMachineUtils;

public class SkufTiltMachine extends SimpleTieredMachine {

    public SkufTiltMachine(IMachineBlockEntity holder, int tier) {
        super(holder, tier, GTMachineUtils.defaultTankSizeFunction);
    }

    @Override
    protected RecipeLogic createRecipeLogic(Object... args) {
        return new SkufTiltRecipeLogic(this);
    }
}
