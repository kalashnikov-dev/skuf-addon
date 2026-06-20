package com.arturgpt.skufaddon;

import com.arturgpt.skufaddon.common.data.SkufBlocks;
import com.arturgpt.skufaddon.common.data.SkufComponentMachines;
import com.arturgpt.skufaddon.common.data.SkufItems;
import com.arturgpt.skufaddon.common.data.SkufMaterials;
import com.arturgpt.skufaddon.common.data.SkufMultiblockMachines;
import com.arturgpt.skufaddon.common.data.SkufRecipeTypes;
import com.arturgpt.skufaddon.common.data.SkufSingleblockMachines;

import com.gregtechceu.gtceu.api.GTCEuAPI;
import com.gregtechceu.gtceu.api.data.chemical.material.event.MaterialEvent;
import com.gregtechceu.gtceu.api.data.chemical.material.event.MaterialRegistryEvent;
import com.gregtechceu.gtceu.api.data.chemical.material.event.PostMaterialEvent;
import com.gregtechceu.gtceu.api.machine.MachineDefinition;
import com.gregtechceu.gtceu.api.recipe.GTRecipeType;
import com.gregtechceu.gtceu.api.registry.registrate.GTRegistrate;
import com.gregtechceu.gtceu.api.sound.SoundEntry;

import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

@Mod(SkufAddon.MOD_ID)
@SuppressWarnings("removal")
public class SkufAddon {

    public static final String MOD_ID = "skufaddon";
    public static final Logger LOGGER = LogManager.getLogger();
    public static final GTRegistrate REGISTRATE = GTRegistrate.create(MOD_ID);

    public SkufAddon() {
        var modEventBus = FMLJavaModLoadingContext.get().getModEventBus();
        modEventBus.addListener(this::commonSetup);
        modEventBus.addListener(this::clientSetup);

        modEventBus.addListener(this::addMaterialRegistries);
        modEventBus.addListener(this::addMaterials);
        modEventBus.addListener(this::modifyMaterials);

        modEventBus.addGenericListener(GTRecipeType.class, this::registerRecipeTypes);
        modEventBus.addGenericListener(MachineDefinition.class, this::registerMachines);
        modEventBus.addGenericListener(SoundEntry.class, this::registerSounds);

        SkufItems.init();
        SkufBlocks.init();
        REGISTRATE.registerRegistrate();
    }

    public static ResourceLocation id(String path) {
        return new ResourceLocation(MOD_ID, path);
    }

    private void commonSetup(final FMLCommonSetupEvent event) {
        event.enqueueWork(() -> LOGGER.info("Skuf Addon common setup complete"));
    }

    private void clientSetup(final FMLClientSetupEvent event) {
        // Client-only initialization goes here.
    }

    private void addMaterialRegistries(MaterialRegistryEvent event) {
        GTCEuAPI.materialManager.createRegistry(MOD_ID);
    }

    private void addMaterials(MaterialEvent event) {
        SkufMaterials.init();
    }

    private void modifyMaterials(PostMaterialEvent event) {}

    private void registerRecipeTypes(GTCEuAPI.RegisterEvent<ResourceLocation, GTRecipeType> event) {
        SkufRecipeTypes.init();
    }

    private void registerMachines(GTCEuAPI.RegisterEvent<ResourceLocation, MachineDefinition> event) {
        SkufSingleblockMachines.init();
        SkufComponentMachines.init();
        SkufMultiblockMachines.init();
    }

    private void registerSounds(GTCEuAPI.RegisterEvent<ResourceLocation, SoundEntry> event) {}
}
