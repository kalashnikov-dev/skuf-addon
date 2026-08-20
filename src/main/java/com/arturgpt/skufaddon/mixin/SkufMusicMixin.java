package com.arturgpt.skufaddon.mixin;

import com.arturgpt.skufaddon.common.data.SkufSounds;

import net.minecraft.client.Minecraft;
import net.minecraft.client.resources.sounds.SoundInstance;
import net.minecraft.client.sounds.MusicManager;
import net.minecraft.core.Holder;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.Music;
import net.minecraft.sounds.SoundEvent;

import org.jetbrains.annotations.Nullable;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

@Mixin(MusicManager.class)
public abstract class SkufMusicMixin {

    private static final int MIN_DELAY_TICKS = 20 * 30;
    private static final int MAX_DELAY_TICKS = 20 * 120;
    private static final List<Integer> TRACK_ORDER = new ArrayList<>();
    private static int trackCursor;

    @Shadow
    private SoundInstance currentMusic;

    @Unique
    @Nullable
    private Music skufaddon$currentMusic;

    @Unique
    @Nullable
    private ResourceLocation skufaddon$currentSituation;

    static {
        refillTrackOrder();
    }

    @Redirect(
              method = "tick",
              at = @At(
                       value = "INVOKE",
                       target = "Lnet/minecraft/client/Minecraft;getSituationalMusic()Lnet/minecraft/sounds/Music;"))
    private Music skufaddon$replaceSituationalMusic(Minecraft minecraft) {
        Music vanillaMusic = minecraft.getSituationalMusic();
        ResourceLocation situation = vanillaMusic.getEvent().value().getLocation();
        boolean situationChanged = !situation.equals(skufaddon$currentSituation);
        boolean currentActive = currentMusic != null && minecraft.getSoundManager().isActive(currentMusic);

        if (skufaddon$currentMusic != null) {
            if (currentMusic == null) {
                return skufaddon$currentMusic;
            }
            if (currentActive && (!situationChanged || !vanillaMusic.replaceCurrentMusic())) {
                return skufaddon$currentMusic;
            }
        }

        skufaddon$currentSituation = situation;
        SoundEvent track = SkufSounds.MUSIC_TRACKS.get(nextTrackIndex()).get();
        skufaddon$currentMusic = new Music(
                Holder.direct(track),
                MIN_DELAY_TICKS,
                MAX_DELAY_TICKS,
                vanillaMusic.replaceCurrentMusic());
        return skufaddon$currentMusic;
    }

    private static int nextTrackIndex() {
        if (trackCursor >= TRACK_ORDER.size()) {
            refillTrackOrder();
        }
        return TRACK_ORDER.get(trackCursor++);
    }

    private static void refillTrackOrder() {
        TRACK_ORDER.clear();
        for (int i = 0; i < SkufSounds.MUSIC_TRACKS.size(); i++) {
            TRACK_ORDER.add(i);
        }
        Collections.shuffle(TRACK_ORDER, ThreadLocalRandom.current());
        trackCursor = 0;
    }
}
