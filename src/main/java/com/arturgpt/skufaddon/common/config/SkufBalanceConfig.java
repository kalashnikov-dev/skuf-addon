package com.arturgpt.skufaddon.common.config;

import net.minecraftforge.common.ForgeConfigSpec;

/**
 * Common configuration for ArthurTech / SkufAddon balance settings.
 * Accessible by both server and client. Saved to run/config/skufaddon-balance.toml.
 */
public final class SkufBalanceConfig {

    public static final ForgeConfigSpec SPEC;

    // --- TILT MECHANICS ---
    public static final ForgeConfigSpec.IntValue MAX_TILT_LEVEL;
    public static final ForgeConfigSpec.IntValue TILT_GROW_INTERVAL_TICKS;
    public static final ForgeConfigSpec.DoubleValue TILT_MULTIPLIER_MAX;
    public static final ForgeConfigSpec.IntValue OVERHEAT_RAMP_TICKS;
    public static final ForgeConfigSpec.IntValue HIDDEN_MODE_DELAY_TICKS;

    // --- HIDDEN TILT (debug / jam debt) ---
    public static final ForgeConfigSpec.IntValue HIDDEN_TILT_MAX;
    public static final ForgeConfigSpec.IntValue HIDDEN_TILT_MISSING_INPUT;
    public static final ForgeConfigSpec.IntValue HIDDEN_TILT_OUTPUT_FULL;
    public static final ForgeConfigSpec.IntValue HIDDEN_TILT_NO_ENERGY;
    public static final ForgeConfigSpec.IntValue HIDDEN_TILT_STALL_PER_SECOND;
    public static final ForgeConfigSpec.IntValue HIDDEN_TILT_STALL_INTERVAL_TICKS;
    public static final ForgeConfigSpec.IntValue HIDDEN_TILT_PAUSED_WHILE_JAMMED;
    public static final ForgeConfigSpec.IntValue HIDDEN_TILT_DENIAL_WHILE_WAITING;
    public static final ForgeConfigSpec.IntValue HIDDEN_TILT_DECAY_INTERVAL_TICKS;
    public static final ForgeConfigSpec.IntValue HIDDEN_TILT_CABLE_BURN_THRESHOLD;
    public static final ForgeConfigSpec.IntValue HIDDEN_TILT_CABLE_BURN_COUNT;
    public static final ForgeConfigSpec.IntValue HIDDEN_TILT_GEAR_EXPLODE_THRESHOLD;

    // --- SAUNA EGORA ---
    public static final ForgeConfigSpec.IntValue SAUNA_BASE_WATER_CONSUME_MB;
    public static final ForgeConfigSpec.IntValue SAUNA_BASE_STEAM_PRODUCE_MB;
    public static final ForgeConfigSpec.IntValue SAUNA_STEAM_BONUS_PER_TIER_MB;
    public static final ForgeConfigSpec.IntValue SAUNA_STEAM_BONUS_PER_TILT_MACHINE_MB;
    public static final ForgeConfigSpec.IntValue SAUNA_DRAIN_INTERVAL_TICKS;

    // --- ENDGAME (LuV -> UHV) ---
    public static final ForgeConfigSpec.DoubleValue DEFECTIVE_MEANING_DECAY_CHANCE;
    public static final ForgeConfigSpec.IntValue VIBE_SINGULARITY_DRAIN_RADIUS;
    public static final ForgeConfigSpec.IntValue VIBE_SINGULARITY_DRAIN_INTERVAL_TICKS;

    // --- RECIPE EUt & DURATIONS ---
    public static final ForgeConfigSpec.IntValue MEMETIC_COLLISION_EUT;
    public static final ForgeConfigSpec.IntValue MEMETIC_COLLISION_DURATION;
    public static final ForgeConfigSpec.IntValue MEANING_STABILIZER_EUT;
    public static final ForgeConfigSpec.IntValue FACTORY_ORDER_CORE_EUT;
    public static final ForgeConfigSpec.IntValue PROVAL_CONCRETE_MIXER_EUT;

    // --- CHELYABINSK PROVAL ---
    public static final ForgeConfigSpec.DoubleValue PROVAL_HAZARD_STRENGTH_PER_PULSE;
    public static final ForgeConfigSpec.IntValue PROVAL_HAZARD_PULSE_INTERVAL_TICKS;
    public static final ForgeConfigSpec.IntValue PROVAL_HAZARD_LOCAL_RADIUS;

    static {
        ForgeConfigSpec.Builder builder = new ForgeConfigSpec.Builder();

        // ---------------- TILT MECHANICS ----------------
        builder.push("tilt");
        MAX_TILT_LEVEL = builder
                .comment("Maximum Tilt Level (УТ) before peak overheat. Default: 100")
                .defineInRange("maxTiltLevel", 100, 1, 1000);

        TILT_GROW_INTERVAL_TICKS = builder
                .comment("Interval in ticks between Tilt level increases during work. Default: 40 (2 sec)")
                .defineInRange("tiltGrowIntervalTicks", 40, 1, 1200);

        TILT_MULTIPLIER_MAX = builder
                .comment("Energy multiplier at 100% Tilt level (e.g. 4.0 = 4x EU/t). Default: 4.0")
                .defineInRange("tiltMultiplierMax", 4.0, 1.0, 20.0);

        OVERHEAT_RAMP_TICKS = builder
                .comment("Ticks spent at peak Tilt before heat intensity reaches 100%. Default: 600 (30 sec)")
                .defineInRange("overheatRampTicks", 600, 20, 3600);

        HIDDEN_MODE_DELAY_TICKS = builder
                .comment("Ticks at max Tilt before machine mode changes to hidden 'Ваще похуй'. Default: 20")
                .defineInRange("hiddenModeDelayTicks", 20, 1, 600);
        builder.pop();

        builder.push("hidden_tilt");
        HIDDEN_TILT_MAX = builder
                .comment("Cap for hidden UT (jam debt). Default: 100")
                .defineInRange("maxHiddenTilt", 100, 1, 1000);
        HIDDEN_TILT_MISSING_INPUT = builder
                .comment("Hidden UT added when a recipe stops for missing input. Default: 5")
                .defineInRange("missingInput", 5, 0, 100);
        HIDDEN_TILT_OUTPUT_FULL = builder
                .comment("Hidden UT added when output is full. Default: 15")
                .defineInRange("outputFull", 15, 0, 100);
        HIDDEN_TILT_NO_ENERGY = builder
                .comment("Hidden UT added when the machine lacks EU. Default: 3")
                .defineInRange("noEnergy", 3, 0, 100);
        HIDDEN_TILT_STALL_PER_SECOND = builder
                .comment("Hidden UT added each stall drip while jammed. Default: 1 every 2 sec (40 ticks)")
                .defineInRange("stallPerSecond", 1, 0, 20);
        HIDDEN_TILT_STALL_INTERVAL_TICKS = builder
                .comment("Ticks between stall drips while jammed. Default: 40 (2 sec, half the old 1/sec rate)")
                .defineInRange("stallIntervalTicks", 40, 1, 1200);
        HIDDEN_TILT_PAUSED_WHILE_JAMMED = builder
                .comment("Hidden UT if the machine is switched off while jammed (denial). Default: 8")
                .defineInRange("pausedWhileJammed", 8, 0, 100);
        HIDDEN_TILT_DENIAL_WHILE_WAITING = builder
                .comment("Extra hidden UT if facade tilt is already in 'Не потеем' / peak while jammed. Default: 4")
                .defineInRange("denialWhileWaiting", 4, 0, 100);
        HIDDEN_TILT_DECAY_INTERVAL_TICKS = builder
                .comment("Ticks between −1 hidden UT while the machine is not jammed. Default: 40 (same as facade tilt)")
                .defineInRange("decayIntervalTicks", 40, 1, 1200);
        HIDDEN_TILT_CABLE_BURN_THRESHOLD = builder
                .comment("Hidden UT at which attached cables melt (GT cable heat). Default: 60")
                .defineInRange("cableBurnThreshold", 60, 1, 1000);
        HIDDEN_TILT_CABLE_BURN_COUNT = builder
                .comment("Max cables melted at the burn threshold (nearest to the machine first). Default: 8")
                .defineInRange("cableBurnCount", 8, 1, 256);
        HIDDEN_TILT_GEAR_EXPLODE_THRESHOLD = builder
                .comment("Hidden UT at which attached transformers/diodes/batteries explode. Default: 90")
                .defineInRange("gearExplodeThreshold", 90, 1, 1000);
        builder.pop();

        // ---------------- SAUNA EGORA ----------------
        builder.push("sauna");
        SAUNA_BASE_WATER_CONSUME_MB = builder
                .comment("Base Water consumption rate in mB/s for Sauna Egora. Default: 80")
                .defineInRange("baseWaterConsumeMB", 80, 1, 10000);

        SAUNA_BASE_STEAM_PRODUCE_MB = builder
                .comment("Base Warm Vibe Steam production rate in mB/s for Sauna Egora. Default: 80")
                .defineInRange("baseSteamProduceMB", 80, 1, 10000);

        SAUNA_STEAM_BONUS_PER_TIER_MB = builder
                .comment("Additional steam output in mB/s per energy hatch tier above EV. Default: 40")
                .defineInRange("steamBonusPerTierMB", 40, 0, 5000);

        SAUNA_STEAM_BONUS_PER_TILT_MACHINE_MB = builder
                .comment("Additional steam output in mB/s per active Tilt machine inside cavity. Default: 60")
                .defineInRange("steamBonusPerTiltMachineMB", 60, 0, 5000);

        SAUNA_DRAIN_INTERVAL_TICKS = builder
                .comment("Interval in ticks between Sauna Egora cooling nearby Tilt machines. Default: 40")
                .defineInRange("tiltDrainIntervalTicks", 40, 1, 1200);
        builder.pop();

        // ---------------- ENDGAME LUV -> UHV ----------------
        builder.push("endgame_luv_uhv");
        DEFECTIVE_MEANING_DECAY_CHANCE = builder
                .comment("Probability of defective_meaning byproduct decay into normie_dust. Default: 0.25 (25%)")
                .defineInRange("defectiveMeaningDecayChance", 0.25, 0.0, 1.0);

        VIBE_SINGULARITY_DRAIN_RADIUS = builder
                .comment("Radius in blocks for Singular Vtykatel (ZPM) regional Tilt suppression. Default: 64")
                .defineInRange("vibeSingularityDrainRadius", 64, 1, 256);

        VIBE_SINGULARITY_DRAIN_INTERVAL_TICKS = builder
                .comment("Interval in ticks for Singular Vtykatel regional Tilt drain. Default: 20 (1 sec)")
                .defineInRange("vibeSingularityDrainIntervalTicks", 20, 1, 1200);
        builder.pop();

        // ---------------- RECIPES ----------------
        builder.push("recipes");
        MEMETIC_COLLISION_EUT = builder
                .comment("EU/t for Memetic Collision recipe in Memetic Collider (LuV). Default: 32768")
                .defineInRange("memeticCollisionEUt", 32768, 1, 2097152);

        MEMETIC_COLLISION_DURATION = builder
                .comment("Duration in ticks for Memetic Collision recipe. Default: 400")
                .defineInRange("memeticCollisionDuration", 400, 1, 72000);

        MEANING_STABILIZER_EUT = builder
                .comment("EU/t for Meaning Stabilizer recipe (LuV). Default: 32768")
                .defineInRange("meaningStabilizerEUt", 32768, 1, 2097152);

        FACTORY_ORDER_CORE_EUT = builder
                .comment("EU/t for Factory Order Core recipe (ZPM). Default: 131072")
                .defineInRange("factoryOrderCoreEUt", 131072, 1, 8388608);

        PROVAL_CONCRETE_MIXER_EUT = builder
                .comment("EU/t for Proval Concrete recipe in Mixer (UV). Default: 524288")
                .defineInRange("provalConcreteMixerEUt", 524288, 1, 33554432);
        builder.pop();

        // ---------------- CHELYABINSK PROVAL ----------------
        builder.push("chelyabinsk_proval");
        PROVAL_HAZARD_STRENGTH_PER_PULSE = builder
                .comment("Radiation charge gained each pulse while Proval crafts; same amount lost each pulse while idle (cool-down). Default: 100 (2× former rate)")
                .defineInRange("hazardStrengthPerPulse", 100.0, 0.0, 1000.0);

        PROVAL_HAZARD_PULSE_INTERVAL_TICKS = builder
                .comment("Ticks between heat/cool pulses. Default: 20 (1 sec)")
                .defineInRange("hazardPulseIntervalTicks", 20, 1, 1200);

        PROVAL_HAZARD_LOCAL_RADIUS = builder
                .comment("Blocks of radiation beyond each extreme face of the formed multiblock (N/S/E/W/up/down). Default: 7")
                .defineInRange("hazardLocalRadius", 7, 0, 64);
        builder.pop();

        SPEC = builder.build();
    }

    private SkufBalanceConfig() {}
}
