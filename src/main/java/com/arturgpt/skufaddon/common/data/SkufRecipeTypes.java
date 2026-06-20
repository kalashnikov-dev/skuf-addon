package com.arturgpt.skufaddon.common.data;

import com.gregtechceu.gtceu.api.capability.recipe.IO;
import com.gregtechceu.gtceu.api.gui.GuiTextures;
import com.gregtechceu.gtceu.api.recipe.GTRecipeType;
import com.gregtechceu.gtceu.common.data.GTSoundEntries;

import com.lowdragmc.lowdraglib.gui.texture.ProgressTexture;

import static com.gregtechceu.gtceu.common.data.GTRecipeTypes.ELECTRIC;
import static com.gregtechceu.gtceu.common.data.GTRecipeTypes.MULTIBLOCK;
import static com.gregtechceu.gtceu.common.data.GTRecipeTypes.register;

public class SkufRecipeTypes {

    public static final GTRecipeType NORMIS_FILTRATION_RECIPES = register("normis_filtration", ELECTRIC)
            .setMaxIOSize(1, 1, 1, 1)
            .setSlotOverlay(true, true, GuiTextures.FLUID_SLOT)
            .setProgressBar(GuiTextures.PROGRESS_BAR_EXTRACT, ProgressTexture.FillDirection.LEFT_TO_RIGHT)
            .setSound(GTSoundEntries.CHEMICAL)
            .setEUIO(IO.IN);

    public static final GTRecipeType SKUFIZATION_RECIPES = register("skufization", MULTIBLOCK)
            .setMaxIOSize(2, 2, 0, 0)
            .setProgressBar(GuiTextures.PROGRESS_BAR_ARROW, ProgressTexture.FillDirection.LEFT_TO_RIGHT)
            .setSound(GTSoundEntries.CHEMICAL)
            .setEUIO(IO.IN);

    /** EMI/JEI info category for passive Diluted Sweat output (actual logic is in {@code SaunaEgoraLogic}). */
    public static final GTRecipeType SAUNA_EGORA_RECIPES = register("sauna_egora", MULTIBLOCK)
            .setMaxIOSize(0, 0, 0, 1)
            .setSlotOverlay(false, false, GuiTextures.FLUID_SLOT)
            .setProgressBar(GuiTextures.PROGRESS_BAR_EXTRACT, ProgressTexture.FillDirection.LEFT_TO_RIGHT)
            .setSound(GTSoundEntries.CHEMICAL)
            .setEUIO(IO.IN)
            .setMaxTooltips(4);

    public static final GTRecipeType CNC_RECIPES = register("cnc_machine", ELECTRIC)
            .setMaxIOSize(3, 1, 1, 0)
            .setEUIO(IO.IN)
            .setProgressBar(GuiTextures.PROGRESS_BAR_EXTRACT, ProgressTexture.FillDirection.LEFT_TO_RIGHT)
            .setSound(GTSoundEntries.MACERATOR)
            .setMaxTooltips(3);

    public static final GTRecipeType POT_DISTILLERY_RECIPES = register("pot_distillery", ELECTRIC)
            .setMaxIOSize(1, 1, 1, 1)
            .setEUIO(IO.IN)
            .setProgressBar(GuiTextures.PROGRESS_BAR_DISTILLATION_TOWER, ProgressTexture.FillDirection.LEFT_TO_RIGHT)
            .setSound(GTSoundEntries.CHEMICAL)
            .setMaxTooltips(3);

    public static final GTRecipeType VIBE_STABILIZER_RECIPES = register("vibe_stabilizer", ELECTRIC)
            .setMaxIOSize(1, 1, 1, 1)
            .setEUIO(IO.IN)
            .setProgressBar(GuiTextures.PROGRESS_BAR_MIXER, ProgressTexture.FillDirection.LEFT_TO_RIGHT)
            .setSound(GTSoundEntries.CHEMICAL)
            .setMaxTooltips(3);

    public static void init() {
        var unused = NORMIS_FILTRATION_RECIPES;
        var unusedMultiblock = SKUFIZATION_RECIPES;
        var unusedSauna = SAUNA_EGORA_RECIPES;
    }
}
