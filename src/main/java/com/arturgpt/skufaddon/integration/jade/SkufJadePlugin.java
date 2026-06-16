package com.arturgpt.skufaddon.integration.jade;

import com.gregtechceu.gtceu.api.blockentity.MetaMachineBlockEntity;

import net.minecraft.world.level.block.Block;

import snownee.jade.api.IWailaClientRegistration;
import snownee.jade.api.IWailaCommonRegistration;
import snownee.jade.api.IWailaPlugin;
import snownee.jade.api.WailaPlugin;

@WailaPlugin
public class SkufJadePlugin implements IWailaPlugin {

    private static final SkufTiltJadeProvider TILT_PROVIDER = new SkufTiltJadeProvider();

    @Override
    public void register(IWailaCommonRegistration registration) {
        registration.registerBlockDataProvider(TILT_PROVIDER, MetaMachineBlockEntity.class);
    }

    @Override
    public void registerClient(IWailaClientRegistration registration) {
        // Jade client API only accepts Block; provider filters by MetaMachineBlockEntity in tooltip.
        registration.registerBlockComponent(TILT_PROVIDER, Block.class);
    }
}
