package com.arturgpt.skufaddon.observer;

import com.arturgpt.skufaddon.SkufAddon;

import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.Executors;

/**
 * Входящий HTTP для агентов (Claude/MCP): localhost-only broadcast в игровой чат.
 *
 * POST /broadcast  {"text":"...", "prefix":"Claude", "triggerBoga": true}
 * Header: Authorization: Bearer &lt;inboundApiKey&gt; (если ключ задан в конфиге)
 */
public final class ObserverInboundHttp {

    private static volatile HttpServer server;
    private static volatile MinecraftServer mc;

    private ObserverInboundHttp() {}

    public static void start(MinecraftServer minecraftServer) {
        if (!ObserverConfig.INBOUND_HTTP_ENABLED.get()) {
            SkufAddon.LOGGER.info("[Observer] inbound HTTP disabled");
            return;
        }
        stop();
        mc = minecraftServer;

        String bind = ObserverConfig.INBOUND_HTTP_BIND.get();
        int port = ObserverConfig.INBOUND_HTTP_PORT.get();
        try {
            HttpServer http = HttpServer.create(new InetSocketAddress(bind, port), 0);
            http.createContext("/broadcast", ObserverInboundHttp::handleBroadcast);
            http.createContext("/health", exchange -> {
                byte[] body = "{\"status\":\"ok\"}".getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().add("Content-Type", "application/json; charset=utf-8");
                exchange.sendResponseHeaders(200, body.length);
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(body);
                }
            });
            http.setExecutor(Executors.newCachedThreadPool(r -> {
                Thread t = new Thread(r, "skuf-observer-inbound");
                t.setDaemon(true);
                return t;
            }));
            http.start();
            server = http;
            SkufAddon.LOGGER.info("[Observer] inbound HTTP listening on {}:{}", bind, port);
        } catch (IOException e) {
            SkufAddon.LOGGER.error("[Observer] failed to start inbound HTTP: {}", e.toString());
        }
    }

    public static void stop() {
        HttpServer http = server;
        server = null;
        if (http != null) {
            http.stop(0);
            SkufAddon.LOGGER.info("[Observer] inbound HTTP stopped");
        }
        mc = null;
    }

    private static void handleBroadcast(HttpExchange exchange) throws IOException {
        try {
            if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
                writeJson(exchange, 405, "{\"ok\":false,\"error\":\"method not allowed\"}");
                return;
            }
            if (!authorize(exchange)) {
                writeJson(exchange, 401, "{\"ok\":false,\"error\":\"unauthorized\"}");
                return;
            }

            String raw = readBody(exchange);
            JsonObject json = JsonParser.parseString(raw).getAsJsonObject();
            if (!json.has("text") || json.get("text").isJsonNull()) {
                writeJson(exchange, 400, "{\"ok\":false,\"error\":\"text required\"}");
                return;
            }
            String text = json.get("text").getAsString().trim();
            if (text.isEmpty()) {
                writeJson(exchange, 400, "{\"ok\":false,\"error\":\"empty text\"}");
                return;
            }
            String prefix = json.has("prefix") && !json.get("prefix").isJsonNull()
                    ? json.get("prefix").getAsString()
                    : "Claude";
            boolean triggerBoga = !json.has("triggerBoga")
                    || json.get("triggerBoga").isJsonNull()
                    || json.get("triggerBoga").getAsBoolean();

            MinecraftServer minecraft = mc;
            if (minecraft == null) {
                writeJson(exchange, 503, "{\"ok\":false,\"error\":\"server not ready\"}");
                return;
            }

            minecraft.execute(() -> {
                ObserverHttpClient.broadcastExternal(minecraft, text, prefix);
                if (triggerBoga) {
                    // Берём любого онлайн-игрока как «носителя» события (нужен ServerPlayer для dimension/pos).
                    ServerPlayer any = null;
                    for (ServerPlayer p : minecraft.getPlayerList().getPlayers()) {
                        any = p;
                        break;
                    }
                    if (any != null) {
                        JsonObject payload = new JsonObject();
                        payload.addProperty("message", text);
                        // player в событии = prefix (Claude), не носитель
                        ObserverHttpClient.sendExternalChatEvent(
                                minecraft, any, prefix, payload);
                    } else {
                        SkufAddon.LOGGER.info(
                                "[Observer] inbound broadcast ok, but no players online — skip Boga");
                    }
                }
            });

            writeJson(exchange, 200, "{\"ok\":true,\"backend\":\"mod\"}");
        } catch (Exception e) {
            SkufAddon.LOGGER.warn("[Observer] inbound /broadcast failed: {}", e.toString());
            writeJson(exchange, 500, "{\"ok\":false,\"error\":\"internal\"}");
        }
    }

    private static boolean authorize(HttpExchange exchange) {
        String expected = ObserverConfig.INBOUND_HTTP_API_KEY.get();
        if (expected == null || expected.isBlank()) {
            return true;
        }
        String auth = exchange.getRequestHeaders().getFirst("Authorization");
        if (auth == null || !auth.regionMatches(true, 0, "Bearer ", 0, 7)) {
            return false;
        }
        return expected.equals(auth.substring(7).trim());
    }

    private static String readBody(HttpExchange exchange) throws IOException {
        try (InputStream in = exchange.getRequestBody()) {
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    private static void writeJson(HttpExchange exchange, int code, String json) throws IOException {
        byte[] body = json.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().add("Content-Type", "application/json; charset=utf-8");
        exchange.sendResponseHeaders(code, body.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(body);
        }
    }
}
