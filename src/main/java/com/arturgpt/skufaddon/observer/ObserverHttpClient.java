package com.arturgpt.skufaddon.observer;

import com.arturgpt.skufaddon.SkufAddon;

import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Тонкий HTTP-клиент: мод → Python sidecar.
 *
 * Важно: запросы идут в ФОНОВОМ потоке.
 * Поток сервера Minecraft (Server thread) нельзя блокировать на сеть —
 * иначе весь мир «замрёт» на время ответа Python/Azure.
 */
public final class ObserverHttpClient {

    /**
     * HTTP/1.1 специально: с HTTP/2 Java HttpClient иногда доставляет
     * на локальный uvicorn пустое тело → FastAPI отвечает 422 Field required.
     */
    private static final HttpClient HTTP = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .connectTimeout(Duration.ofSeconds(2))
            .build();

    /** Один фоновый поток для исходящих запросов наблюдателя. */
    private static final ExecutorService WORKER = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "skuf-observer-http");
        t.setDaemon(true); // не мешает JVM выключиться вместе с сервером
        return t;
    });

    /** Когда последний раз писали в чат (millis). 0 = ещё никогда. */
    private static volatile long lastAnnounceMillis = 0L;

    private ObserverHttpClient() {}

    /**
     * Антиспам для обычных событий.
     *
     * @param important true = важное (death / advancement / dimension) — всегда в чат,
     *                  и сбрасываем таймер кулдауна (следующие «обычные» ждут снова 5 мин).
     */
    public static boolean tryAcquireAnnounceSlot(boolean important) {
        long now = System.currentTimeMillis();
        long cooldownMs = ObserverConfig.COOLDOWN_SECONDS.get() * 1000L;
        synchronized (ObserverHttpClient.class) {
            if (!important && lastAnnounceMillis != 0L && (now - lastAnnounceMillis) < cooldownMs) {
                SkufAddon.LOGGER.info(
                        "[Observer] skipped ordinary event (cooldown {}s still active)",
                        ObserverConfig.COOLDOWN_SECONDS.get());
                return false;
            }
            if (important) {
                SkufAddon.LOGGER.info("[Observer] important event — bypassing cooldown");
            }
            lastAnnounceMillis = now;
            return true;
        }
    }

    /**
     * Отправить одно событие и (если Python вернул comment) написать его в чат.
     *
     * @param important если true — игнорирует 5‑минутный лимит
     */
    public static void sendEventAndAnnounce(
                                            MinecraftServer server,
                                            ServerPlayer player,
                                            String type,
                                            JsonObject payload,
                                            boolean important) {
        if (!ObserverConfig.ENABLED.get()) {
            return;
        }
        if (!tryAcquireAnnounceSlot(important)) {
            return;
        }

        String baseUrl = ObserverConfig.BASE_URL.get();
        String apiKey = ObserverConfig.API_KEY.get();
        String playerName = player.getGameProfile().getName();

        // Список ников онлайн — Python потом использует в промпте
        JsonArray online = new JsonArray();
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            online.add(p.getGameProfile().getName());
        }

        JsonObject event = new JsonObject();
        event.addProperty("event_id", UUID.randomUUID().toString());
        event.addProperty("timestamp", System.currentTimeMillis() / 1000.0);
        event.addProperty("player", playerName);
        event.addProperty("type", type);
        event.add("payload", payload != null ? payload : new JsonObject());
        event.addProperty("dimension", player.level().dimension().location().toString());
        event.add("pos", posArray(player.getBlockX(), player.getBlockY(), player.getBlockZ()));

        JsonArray events = new JsonArray();
        events.add(event);

        JsonObject body = new JsonObject();
        body.add("events", events);
        body.add("online_players", online);

        String json = body.toString();
        byte[] jsonBytes = json.getBytes(StandardCharsets.UTF_8);

        WORKER.execute(() -> {
            try {
                int timeoutSec = ObserverConfig.REQUEST_TIMEOUT_SECONDS.get();
                SkufAddon.LOGGER.info(
                        "[Observer] POST {}/events ({} bytes, timeout {}s)",
                        trimSlash(baseUrl),
                        jsonBytes.length,
                        timeoutSec);

                HttpRequest.Builder req = HttpRequest.newBuilder()
                        .uri(URI.create(trimSlash(baseUrl) + "/events"))
                        .timeout(Duration.ofSeconds(timeoutSec))
                        .header("Content-Type", "application/json; charset=utf-8")
                        .POST(HttpRequest.BodyPublishers.ofByteArray(jsonBytes));

                if (apiKey != null && !apiKey.isBlank()) {
                    req.header("Authorization", "Bearer " + apiKey);
                }

                HttpResponse<String> response = HTTP.send(req.build(), HttpResponse.BodyHandlers.ofString());
                if (response.statusCode() < 200 || response.statusCode() >= 300) {
                    SkufAddon.LOGGER.warn(
                            "[Observer] Python returned HTTP {}: {}",
                            response.statusCode(),
                            response.body());
                    return;
                }

                String comment = parseComment(response.body());
                if (comment == null || comment.isBlank()) {
                    SkufAddon.LOGGER.info("[Observer] Python returned no comment (null)");
                    return;
                }

                // Чат можно трогать только на Server thread
                final String text = comment;
                server.execute(() -> broadcast(server, text));
            } catch (Exception e) {
                // Fail-open: игра живёт, даже если Python выключен
                SkufAddon.LOGGER.warn("[Observer] Failed to reach Python sidecar: {}", e.toString());
            }
        });
    }

    private static void broadcast(MinecraftServer server, String comment) {
        String prefix = ObserverConfig.CHAT_PREFIX.get();
        if (prefix == null || prefix.isBlank()) {
            prefix = "Бог А";
        }
        // Модель иногда сама начинает с «Бог А» / «[Бог А]» / «<Бог А>» — убираем дубль
        String text = stripLeadingPrefix(comment.trim(), prefix);
        Component message = Component.literal("<" + prefix + "> " + text);
        List<ServerPlayer> players = server.getPlayerList().getPlayers();
        for (ServerPlayer p : players) {
            p.sendSystemMessage(message);
        }
        SkufAddon.LOGGER.info("[Observer] chat: {}", text);
    }

    /** Срезает ведущий префикс вида «Бог А», «[Бог А]», «<Бог А>», «Бог А:». */
    private static String stripLeadingPrefix(String comment, String prefix) {
        String t = comment;
        String[] variants = {
                "<" + prefix + ">",
                "[" + prefix + "]",
                prefix
        };
        for (String variant : variants) {
            if (t.startsWith(variant)) {
                t = t.substring(variant.length()).trim();
                break;
            }
        }
        if (t.startsWith(":") || t.startsWith("—") || t.startsWith("-")) {
            t = t.substring(1).trim();
        }
        return t;
    }

    private static String parseComment(String body) {
        JsonObject obj = JsonParser.parseString(body).getAsJsonObject();
        if (!obj.has("comment") || obj.get("comment").isJsonNull()) {
            return null;
        }
        return obj.get("comment").getAsString();
    }

    private static JsonArray posArray(int x, int y, int z) {
        JsonArray pos = new JsonArray();
        pos.add(x);
        pos.add(y);
        pos.add(z);
        return pos;
    }

    private static String trimSlash(String url) {
        if (url.endsWith("/")) {
            return url.substring(0, url.length() - 1);
        }
        return url;
    }
}
