package com.arturgpt.skufaddon.common.data;

import com.gregtechceu.gtceu.api.capability.recipe.IO;
import com.gregtechceu.gtceu.api.gui.GuiTextures;
import com.gregtechceu.gtceu.api.recipe.GTRecipeType;
import com.gregtechceu.gtceu.common.data.GTSoundEntries;

import com.lowdragmc.lowdraglib.gui.texture.ProgressTexture;

import static com.gregtechceu.gtceu.common.data.GTRecipeTypes.ELECTRIC;
import static com.gregtechceu.gtceu.common.data.GTRecipeTypes.register;

public class SkufRecipeTypes {

    public static final GTRecipeType NORMIS_FILTRATION_RECIPES = register("normis_filtration", ELECTRIC)
            .setMaxIOSize(1, 1, 1, 1)
            .setSlotOverlay(true, true, GuiTextures.FLUID_SLOT)
            .setProgressBar(GuiTextures.PROGRESS_BAR_ARROW, ProgressTexture.FillDirection.LEFT_TO_RIGHT)
            .setSound(GTSoundEntries.CHEMICAL)
            .setEUIO(IO.IN);

    public static void init() {
        // Ensures static fields are initialized during GTCEu recipe type registration.
        var unused = NORMIS_FILTRATION_RECIPES;
    }
}
