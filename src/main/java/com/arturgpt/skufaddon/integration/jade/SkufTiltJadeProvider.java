package com.arturgpt.skufaddon.integration.jade;

import com.arturgpt.skufaddon.SkufAddon;
import com.arturgpt.skufaddon.common.machine.singleblock.tilt.SkufTiltRecipeLogic;

import com.gregtechceu.gtceu.api.blockentity.MetaMachineBlockEntity;
import com.gregtechceu.gtceu.api.machine.MetaMachine;
import com.gregtechceu.gtceu.api.machine.WorkableTieredMachine;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.entity.BlockEntity;

import snownee.jade.api.BlockAccessor;
import snownee.jade.api.IBlockComponentProvider;
import snownee.jade.api.IServerDataProvider;
import snownee.jade.api.ITooltip;
import snownee.jade.api.config.IPluginConfig;

/**
 * Sole Jade source for tilt status (voltage / mode). Kept off RecipeLogic fancy
 * tooltips so idle machines do not get a false {@code Fail to setup recipe:} line.
 */
public class SkufTiltJadeProvider implements IBlockComponentProvider, IServerDataProvider<BlockAccessor> {

    public static final ResourceLocation UID = SkufAddon.id("tilt_provider");

    private static final String KEY_HAS_TILT = "SkufHasTilt";
    private static final String KEY_LINE_COUNT = "SkufTiltLines";
    private static final String KEY_LINE_PREFIX = "SkufTiltLine";

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

        var lines = tiltLogic.getTiltStatusTooltip();
        data.putBoolean(KEY_HAS_TILT, true);
        data.putInt(KEY_LINE_COUNT, lines.size());
        for (int i = 0; i < lines.size(); i++) {
            data.putString(KEY_LINE_PREFIX + i, Component.Serializer.toJson(lines.get(i)));
        }
    }

    @Override
    public void appendTooltip(ITooltip tooltip, BlockAccessor accessor, IPluginConfig config) {
        CompoundTag data = accessor.getServerData();
        if (!data.getBoolean(KEY_HAS_TILT)) {
            return;
        }
        int count = data.getInt(KEY_LINE_COUNT);
        for (int i = 0; i < count; i++) {
            Component line = Component.Serializer.fromJson(data.getString(KEY_LINE_PREFIX + i));
            if (line != null) {
                tooltip.add(line);
            }
        }
    }
}
