package com.arturgpt.skufaddon.observer;

import com.arturgpt.skufaddon.SkufAddon;

import net.minecraft.advancements.Advancement;
import net.minecraft.advancements.DisplayInfo;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.level.Level;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.ServerChatEvent;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.player.AdvancementEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;

import com.google.gson.JsonObject;

/**
 * «Уши» наблюдателя.
 *
 * Обычные (join) — не чаще раз в cooldownSeconds (~5 мин).
 * Важные (death, advancement, dimension) — всегда.
 * Чат — каждое сообщение уходит в ИИ; отвечать или молчать решает модель.
 */
public final class ObserverEvents {

    private ObserverEvents() {}

    public static void init() {
        MinecraftForge.EVENT_BUS.register(new ObserverEvents());
        SkufAddon.LOGGER.info(
                "Observer events registered " +
                        "(join=ordinary; death/advancement/dimension=important; chat=always-analyze)");
    }

    @SubscribeEvent
    public void onServerStarted(ServerStartedEvent event) {
        ObserverInboundHttp.start(event.getServer());
    }

    @SubscribeEvent
    public void onServerStopping(ServerStoppingEvent event) {
        ObserverInboundHttp.stop();
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
                false);
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

    /**
     * Любое сообщение в чате → ИИ сам решает: ответить или SKIP.
     */
    @SubscribeEvent
    public void onServerChat(ServerChatEvent event) {
        if (!ObserverConfig.ENABLED.get()) {
            return;
        }

        String raw = event.getRawText();
        if (raw == null || raw.isBlank()) {
            return;
        }
        // Команды (/gamemode и т.п.) не анализируем
        if (raw.trim().startsWith("/")) {
            return;
        }

        ServerPlayer player = event.getPlayer();
        JsonObject payload = new JsonObject();
        payload.addProperty("message", raw);

        SkufAddon.LOGGER.info(
                "[Observer] chat: {} -> '{}'", player.getGameProfile().getName(), raw);

        ObserverHttpClient.sendEventAndAnnounce(
                player.getServer(),
                player,
                "chat",
                payload,
                false,
                true);
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
                true);
    }

    /**
     * Ачивка (не recipe-unlock) — редкий мемный момент прогресса.
     */
    @SubscribeEvent
    public void onAdvancementEarn(AdvancementEvent.AdvancementEarnEvent event) {
        if (!ObserverConfig.ENABLED.get()) {
            return;
        }
        if (event.getEntity().level().isClientSide()) {
            return;
        }
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }

        Advancement advancement = event.getAdvancement();
        ResourceLocation id = advancement.getId();
        DisplayInfo display = advancement.getDisplay();

        // Recipe-book unlock'и спамят и часто без display — пропускаем
        if (display == null || id.getPath().startsWith("recipes/")) {
            return;
        }

        JsonObject payload = new JsonObject();
        payload.addProperty("advancement_id", id.toString());
        payload.addProperty("title", display.getTitle().getString());
        payload.addProperty("frame", display.getFrame().getName());

        SkufAddon.LOGGER.info(
                "[Observer] advancement: {} -> {} ({})",
                player.getGameProfile().getName(),
                id,
                display.getTitle().getString());

        ObserverHttpClient.sendEventAndAnnounce(
                player.getServer(),
                player,
                "advancement",
                payload,
                true);
    }

    /**
     * Смена измерения (Nether / End / кастом) — всегда повод для реплики.
     */
    @SubscribeEvent
    public void onDimensionChange(PlayerEvent.PlayerChangedDimensionEvent event) {
        if (!ObserverConfig.ENABLED.get()) {
            return;
        }
        if (event.getEntity().level().isClientSide()) {
            return;
        }
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }

        ResourceKey<Level> from = event.getFrom();
        ResourceKey<Level> to = event.getTo();

        JsonObject payload = new JsonObject();
        payload.addProperty("from", from.location().toString());
        payload.addProperty("to", to.location().toString());

        SkufAddon.LOGGER.info(
                "[Observer] dimension: {} {} -> {}",
                player.getGameProfile().getName(),
                from.location(),
                to.location());

        ObserverHttpClient.sendEventAndAnnounce(
                player.getServer(),
                player,
                "dimension",
                payload,
                true);
    }
}
