package com.arturgpt.skufaddon.integration.jade;

import com.arturgpt.skufaddon.SkufAddon;
import com.arturgpt.skufaddon.common.machine.tilt.SkufTiltRecipeLogic;
import com.arturgpt.skufaddon.common.machine.tilt.SkufTiltUtils;

import com.gregtechceu.gtceu.api.blockentity.MetaMachineBlockEntity;
import com.gregtechceu.gtceu.api.machine.MetaMachine;
import com.gregtechceu.gtceu.api.machine.WorkableTieredMachine;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.entity.BlockEntity;

import snownee.jade.api.BlockAccessor;
import snownee.jade.api.IBlockComponentProvider;
import snownee.jade.api.IServerDataProvider;
import snownee.jade.api.ITooltip;
import snownee.jade.api.config.IPluginConfig;

public class SkufTiltJadeProvider implements IBlockComponentProvider, IServerDataProvider<BlockAccessor> {

    public static final ResourceLocation UID = SkufAddon.id("tilt_provider");

    private static final String KEY_TILT_LEVEL = "SkufTiltLevel";
    private static final String KEY_TICKS_AT_MAX = "SkufTiltMaxTicks";

    @Override
    public ResourceLocation getUid() {
        return UID;
    }

    @Override
    public void appendServerData(CompoundTag data, BlockAccessor accessor) {
        BlockEntity be = accessor.getBlockEntity();
        if (!(be instanceof MetaMachineBlockEntity mmbe)) {
            return;
        }
        MetaMachine machine = mmbe.getMetaMachine();
        if (!(machine instanceof WorkableTieredMachine workable)) {
            return;
        }
        if (!(workable.getRecipeLogic() instanceof SkufTiltRecipeLogic tiltLogic)) {
            return;
        }

        data.putInt(KEY_TILT_LEVEL, tiltLogic.getTiltLevel());
        data.putInt(KEY_TICKS_AT_MAX, tiltLogic.getTicksAtMaxTilt());
    }

    @Override
    public void appendTooltip(ITooltip tooltip, BlockAccessor accessor, IPluginConfig config) {
        if (!(accessor.getBlockEntity() instanceof MetaMachineBlockEntity)) {
            return;
        }
        CompoundTag data = accessor.getServerData();
        if (!data.contains(KEY_TILT_LEVEL)) {
            return;
        }

        int tiltLevel = data.getInt(KEY_TILT_LEVEL);
        int ticksAtMaxTilt = data.getInt(KEY_TICKS_AT_MAX);
        tooltip.add(SkufTiltUtils.getModeComponent(tiltLevel, ticksAtMaxTilt));
    }
}
