package com.arturgpt.skufaddon.common.data;

import com.arturgpt.skufaddon.SkufAddon;

import net.minecraft.world.item.Item;

import com.tterrag.registrate.util.entry.ItemEntry;

/**
 * Standalone items that are not tied to the GregTech material system.
 * For material-based items (ingots, gears, bolts, etc.) use {@link SkufMaterials} instead.
 * Tiered hull-style blocks live in {@link SkufComponentMachines}.
 */
public class SkufItems {

    public static ItemEntry<Item> PRAVILNAYA_VESH;

    public static ItemEntry<Item> CNC_BIT;
    public static ItemEntry<Item> CNC_CUTTER;

    public static ItemEntry<Item> DODIK_CIRCUIT_BASIC;
    public static ItemEntry<Item> DODIK_CIRCUIT_ADVANCED;
    public static ItemEntry<Item> DODIK_CIRCUIT_EXTREME;

    public static ItemEntry<Item> MELTED_CAPACITOR;
    public static ItemEntry<Item> BURNT_CABLE_DEBRIS;
    public static ItemEntry<Item> CHARRED_DEVELOPER_CIRCUIT;

    public static ItemEntry<Item> MYPOSHKO_SCRIPT;
    public static ItemEntry<Item> EGOR_CORE;

    public static ItemEntry<Item> CORRECT_MATTER_MICROCAPSULE;
    public static ItemEntry<Item> ANTIZOOMER_CORE;
    public static ItemEntry<Item> CORRECT_DEVELOPER_SCHEMATIC;
    public static ItemEntry<Item> NORMIS_SINGULARITY;
    public static ItemEntry<Item> ABSOLUTE_POHUIT;
    public static ItemEntry<Item> ARTURIAN_MAINFRAME;

    public static ItemEntry<Item> RAW_DEMO;

    public static void init() {
        PRAVILNAYA_VESH = SkufAddon.REGISTRATE
                .item("pravilnaya_vesh", Item::new)
                .register();

        CNC_BIT = SkufAddon.REGISTRATE
                .item("cnc_bit", Item::new)
                .register();

        CNC_CUTTER = SkufAddon.REGISTRATE
                .item("cnc_cutter", Item::new)
                .register();

        DODIK_CIRCUIT_BASIC = SkufAddon.REGISTRATE
                .item("dodik_circuit_basic", Item::new)
                .register();

        DODIK_CIRCUIT_ADVANCED = SkufAddon.REGISTRATE
                .item("dodik_circuit_advanced", Item::new)
                .register();

        DODIK_CIRCUIT_EXTREME = SkufAddon.REGISTRATE
                .item("dodik_circuit_extreme", Item::new)
                .register();

        MELTED_CAPACITOR = SkufAddon.REGISTRATE
                .item("melted_capacitor", Item::new)
                .register();

        BURNT_CABLE_DEBRIS = SkufAddon.REGISTRATE
                .item("burnt_cable_debris", Item::new)
                .register();

        CHARRED_DEVELOPER_CIRCUIT = SkufAddon.REGISTRATE
                .item("charred_developer_circuit", Item::new)
                .register();

        MYPOSHKO_SCRIPT = SkufAddon.REGISTRATE
                .item("myposhko_script", Item::new)
                .register();

        EGOR_CORE = SkufAddon.REGISTRATE
                .item("egor_core", Item::new)
                .register();

        CORRECT_MATTER_MICROCAPSULE = SkufAddon.REGISTRATE
                .item("correct_matter_microcapsule", Item::new)
                .register();

        ANTIZOOMER_CORE = SkufAddon.REGISTRATE
                .item("antizoomer_core", Item::new)
                .register();

        CORRECT_DEVELOPER_SCHEMATIC = SkufAddon.REGISTRATE
                .item("correct_developer_schematic", Item::new)
                .register();

        NORMIS_SINGULARITY = SkufAddon.REGISTRATE
                .item("normis_singularity", Item::new)
                .register();

        ABSOLUTE_POHUIT = SkufAddon.REGISTRATE
                .item("absolute_pohuit", Item::new)
                .register();

        ARTURIAN_MAINFRAME = SkufAddon.REGISTRATE
                .item("arturian_mainframe", Item::new)
                .register();

        RAW_DEMO = SkufAddon.REGISTRATE
                .item("raw_demo", Item::new)
                .register();
    }
}
