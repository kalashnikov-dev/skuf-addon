# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**SkufAddon** (mod ID: `skufaddon`) — GregTech CEu Modern addon for Minecraft 1.20.1 Forge.
Internal name: ArthurTech. Java 17, GTCEu 7.5.1, LDLib 1.0.40.b. Build JDK: 17+ (verified with JDK 21).

## Build Commands

```bash
# Set JAVA_HOME first (required: JDK 17+)
export JAVA_HOME="/path/to/jdk-21"

# Build the mod jar
./gradlew build --no-daemon

# Run client (launch game with mod)
./gradlew runClient --no-daemon

# Regenerate item models, lang, blockstates (data gen)
./gradlew runData --no-daemon

# Apply code formatting (Spotless)
./gradlew spotlessApply

# Full clean build
./gradlew clean build --no-daemon
```

Convenience scripts: `run.bat` (Windows) / `run.sh` (Git Bash) auto-detect JDK 17+ and prompt for action.

## Architecture

### Entry Points

- **`SkufAddon`** — `@Mod` entry. Creates `GTRegistrate`, registers materials, recipe types, machines, blocks, effects, network channel.
- **`SkufGTAddon`** — `@GTAddon` implements `IGTAddon`. Registers recipes via `SkufRecipes.init()` and ore veins via `SkufOres.init()`.

### Registration Pattern

All game objects use **GTRegistrate** (Registrate-based builder pattern from GTCEu):

```java
SkufAddon.REGISTRATE.machine("name", holder -> new SkufTiltMachine(holder, tier))
    .lang(...)
    .recipeType(recipeType)
    .register();
```

Materials are registered in `SkufMaterials.init()` using `Material.Builder` with GTCEu material system.

### Key Packages

| Package | Purpose |
|---------|---------|
| `common.data` | Registration classes: `SkufMaterials`, `SkufMachines` (legacy), `SkufSingleblockMachines`, `SkufMultiblockMachines`, `SkufBlocks`, `SkufItems`, `SkufRecipes`, `SkufOres` |
| `aura` | Per-chunk "Entropy & Vibe" aura system (SavedData). `ArthurAura` stores entropy/vibe per chunk. `AuraHandler` ticks every ~5s. `AuraRecipeModifier` modifies recipes based on local vibe. |
| `machine` | Custom machine classes: `GameplayReviewMachine`, `MyposhkoPortMachine`, `PukanIndicatorMachine` |
| `machine.multiblock` | Multiblock machines: `EmergencyIgnoranceMachine`, `SaunaEgoraMachine` |
| `machine.singleblock.tilt` | `SkufTiltMachine` extends `SimpleTieredMachine` — base for all aura-aware singleblock machines |
| `mechanics` | Game mechanics: `LineMode`, `LineModeModifier`, `MyposhkoModifier`/`MyposhkoState`, `IgnoranceConfig`/`IgnoranceState`, `PukanFormula`, `StasisField`, `EndgameGate`, `SaunaCoolingState` |
| `client` | Client-side: `ClientAuraState`, `SkufClientOverlay` (HUD rendering) |
| `network` | `SkufNetwork` — `SimpleChannel` for aura sync (client↔server) |
| `item` | Special items: `LyrikaCapsuleItem`, `DerevenskiyPokoyItem` |
| `api.machine` | Interfaces: `ISaunaProvider`, `ISaunaReceiver` |

### Aura & Tilt Systems

**ArthurAura** (`aura/ArthurAura.java`) — `SavedData` storing per-chunk `{entropy, vibe}` floats (0–100). Vibe baseline is 20. High entropy destabilizes machines. Ticks every ~5s via `AuraHandler`. Syncs to clients via `SkufNetwork` packets.

**MachineTilt** (`aura/MachineTilt.java`) — separate `SavedData`, per-machine float (0–100) keyed by `BlockPos`. Grows during work and sharply on stall. At 100% triggers "Burning Pukan" (entropy burst, tilt reset). Sauna Egora cools nearby machines via `drainRadius()`.

**Sauna pattern:** Machines implement `ISaunaReceiver` (`api.machine`), the Sauna Egora multiblock implements `ISaunaProvider`. They bind/unbind during multiblock structure formation.

### Line Mode

Per-chunk enum (`mechanics/LineMode.java`) affecting all machines in chunk:
- **UGAR** (Hype): 1.4x speed, 1.1x pukan heat
- **POT** (Sweat): 1.0x — default
- **NE_POTEEM** (No Sweat): 0.75x speed, 0.9x heat
- **POHUI** (Whatever): 1.0x speed, 0.8x heat

Applied via `LineModeModifier` + `LineModeState` (SavedData).

### Recipes

Recipes are defined in `SkufRecipes.init(Consumer<FinishedRecipe>)` called from `SkufGTAddon.addRecipes()`. Uses GTCEu recipe builder pattern: `recipeType.recipeBuilder("name").inputItems(...).outputItems(...).duration(...).EUt(...).save(provider)`. Standard tag prefixes (`ingot`, `dust`, `gem`, `plate`, etc.) are imported statically.

### Known Issues

- **`src/generated/` has duplicates of `src/main/resources/`** — `processResources` can fail. Delete `src/generated/` if you see resource conflicts.
- `SkufMachines.java` in root package is legacy; the canonical registration moved to `common.data.SkufSingleblockMachines` and `common.data.SkufMultiblockMachines`.

## Andrej Karpathy LLM Coding Guidelines

1. **Think Before Coding**: State assumptions explicitly. Surface tradeoffs. Don't pick silently when multiple interpretations exist. Push back when warranted. Stop when confused.
2. **Simplicity First**: Minimum code that solves the problem. Nothing speculative. No features beyond what was asked. No abstractions for single-use code. If you write 200 lines and it could be 50, rewrite it.
3. **Surgical Changes**: Touch only what you must. Clean up only your own mess. Match existing style. Remove imports/variables/functions that your changes made unused.
4. **Goal-Driven Execution**: Define success criteria. Loop until verified. For multi-step tasks, state a brief plan with verification checks.

