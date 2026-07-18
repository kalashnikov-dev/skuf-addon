package com.arturgpt.skufaddon.observer;

import com.arturgpt.skufaddon.SkufAddon;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;

import com.google.gson.JsonObject;

/**
 * «Уши» наблюдателя.
 *
 * Обычные события (join) — не чаще раз в cooldownSeconds (~5 мин).
 * Важные (death) — всегда комментируются, лимит игнорируется.
 */
public final class ObserverEvents {

    private ObserverEvents() {}

    public static void init() {
        MinecraftForge.EVENT_BUS.register(new ObserverEvents());
        SkufAddon.LOGGER.info("Observer events registered (join=ordinary, death=important)");
    }

    @SubscribeEvent
    public void onPlayerLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (!ObserverConfig.ENABLED.get()) {
            return;
        }
        if (event.getEntity().level().isClientSide()) {
            return;
        }
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }

        String name = player.getGameProfile().getName();
        SkufAddon.LOGGER.info("[Observer] player joined: {}", name);

        ObserverHttpClient.sendEventAndAnnounce(
                player.getServer(),
                player,
                "join",
                new JsonObject(),
                false); // обычное — ждёт 5 минут
    }

    @SubscribeEvent
    public void onPlayerLogout(PlayerEvent.PlayerLoggedOutEvent event) {
        if (!ObserverConfig.ENABLED.get()) {
            return;
        }
        if (event.getEntity().level().isClientSide()) {
            return;
        }

        String name = event.getEntity().getGameProfile().getName();
        SkufAddon.LOGGER.info("[Observer] player left: {}", name);
    }

    @SubscribeEvent
    public void onLivingDeath(LivingDeathEvent event) {
        if (!ObserverConfig.ENABLED.get()) {
            return;
        }
        if (event.getEntity().level().isClientSide()) {
            return;
        }
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }

        DamageSource source = event.getSource();
        String cause = source.getMsgId();

        JsonObject payload = new JsonObject();
        payload.addProperty("cause", cause);

        SkufAddon.LOGGER.info("[Observer] player died: {} ({})", player.getGameProfile().getName(), cause);

        ObserverHttpClient.sendEventAndAnnounce(
                player.getServer(),
                player,
                "death",
                payload,
                true); // важное — без лимита 5 минут
    }
}
