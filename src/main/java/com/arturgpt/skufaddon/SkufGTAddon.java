package com.arturgpt.skufaddon;

import com.arturgpt.skufaddon.common.data.SkufOres;
import com.arturgpt.skufaddon.common.data.SkufRecipes;

import com.gregtechceu.gtceu.api.addon.GTAddon;
import com.gregtechceu.gtceu.api.addon.IGTAddon;
import com.gregtechceu.gtceu.api.registry.registrate.GTRegistrate;

import net.minecraft.data.recipes.FinishedRecipe;

import java.util.function.Consumer;

@SuppressWarnings("unused")
@GTAddon
public class SkufGTAddon implements IGTAddon {

    @Override
    public GTRegistrate getRegistrate() {
        return SkufAddon.REGISTRATE;
    }

    @Override
    public void initializeAddon() {}

    @Override
    public String addonModId() {
        return SkufAddon.MOD_ID;
    }

    @Override
    public void registerTagPrefixes() {}

    @Override
    public void addRecipes(Consumer<FinishedRecipe> provider) {
        SkufRecipes.init(provider);
    }

    @Override
    public void registerElements() {}

    @Override
    public void registerOreVeins() {
        SkufOres.init();
    }
}
