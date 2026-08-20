package com.arturgpt.skufaddon.common.data;

import com.arturgpt.skufaddon.SkufAddon;

import net.minecraft.sounds.SoundEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public final class SkufSounds {

    public static final DeferredRegister<SoundEvent> SOUNDS = DeferredRegister.create(ForgeRegistries.SOUND_EVENTS,
            SkufAddon.MOD_ID);
    public static final List<RegistryObject<SoundEvent>> MUSIC_TRACKS = registerMusicTracks();

    private SkufSounds() {}

    public static void init(IEventBus modEventBus) {
        SOUNDS.register(modEventBus);
    }

    private static List<RegistryObject<SoundEvent>> registerMusicTracks() {
        var tracks = new ArrayList<RegistryObject<SoundEvent>>();
        for (int i = 1; i <= 18; i++) {
            String trackId = String.format(Locale.ROOT, "%02d", i);
            String eventId = "music_track_" + trackId;
            tracks.add(SOUNDS.register(eventId,
                    () -> SoundEvent.createVariableRangeEvent(SkufAddon.id(eventId))));
        }
        return List.copyOf(tracks);
    }
}
