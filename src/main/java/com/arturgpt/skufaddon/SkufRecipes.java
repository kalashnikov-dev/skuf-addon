package com.arturgpt.skufaddon;

import com.gregtechceu.gtceu.common.data.GTRecipeTypes;

import net.minecraft.data.recipes.FinishedRecipe;

import java.util.function.Consumer;

public class SkufRecipes {

    public static void init(Consumer<FinishedRecipe> provider) {
        GTRecipeTypes.CHEMICAL_RECIPES.recipeBuilder("jizhnyak_mixing")
                .inputFluids(SkufMaterials.sweat.getFluid(1000))
                .inputFluids(SkufMaterials.puffSmoke.getFluid(1000))
                .outputFluids(SkufMaterials.jizhnyak.getFluid(1000))
                .duration(200)
                .EUt(30)
                .save(provider);

        GTRecipeTypes.CENTRIFUGE_RECIPES.recipeBuilder("jizhnyak_separation")
                .inputFluids(SkufMaterials.jizhnyak.getFluid(1000))
                .outputFluids(SkufMaterials.sweat.getFluid(1000))
                .outputFluids(SkufMaterials.puffSmoke.getFluid(1000))
                .duration(400)
                .EUt(30)
                .save(provider);
    }
}
