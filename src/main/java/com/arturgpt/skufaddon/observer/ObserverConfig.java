package com.arturgpt.skufaddon.observer;

import net.minecraftforge.common.ForgeConfigSpec;

/**
 * Настройки ИИ-наблюдателя (серверные).
 *
 * Файл после запуска: run/config/skufaddon-observer.toml
 */
public final class ObserverConfig {

    public static final ForgeConfigSpec SPEC;

    public static final ForgeConfigSpec.BooleanValue ENABLED;
    public static final ForgeConfigSpec.ConfigValue<String> BASE_URL;
    public static final ForgeConfigSpec.ConfigValue<String> API_KEY;

    /**
     * Пауза между «обычными» комментариями (join и т.п.).
     * Важные события (death и т.п.) этот лимит игнорируют.
     * 300 = примерно раз в 5 минут.
     */
    public static final ForgeConfigSpec.IntValue COOLDOWN_SECONDS;

    public static final ForgeConfigSpec.IntValue REQUEST_TIMEOUT_SECONDS;

    /** Префикс в чате, например «Бог А» → сообщение вида «&lt;Бог А&gt; …». */
    public static final ForgeConfigSpec.ConfigValue<String> CHAT_PREFIX;

    /**
     * Входящий HTTP (Claude/MCP → игровой чат). Только bind localhost.
     * Python sidecar шлёт сюда при SEND_CHAT_BACKEND=mod.
     */
    public static final ForgeConfigSpec.BooleanValue INBOUND_HTTP_ENABLED;
    public static final ForgeConfigSpec.ConfigValue<String> INBOUND_HTTP_BIND;
    public static final ForgeConfigSpec.IntValue INBOUND_HTTP_PORT;
    public static final ForgeConfigSpec.ConfigValue<String> INBOUND_HTTP_API_KEY;

    static {
        ForgeConfigSpec.Builder builder = new ForgeConfigSpec.Builder();

        builder.push("observer");

        ENABLED = builder
                .comment("Enable AI observer (sends events to the Python sidecar).")
                .define("enabled", true);

        BASE_URL = builder
                .comment("Python sidecar base URL (no trailing slash).")
                .define("baseUrl", "http://127.0.0.1:8080");

        API_KEY = builder
                .comment("Shared secret sent as Bearer token. Empty = no Authorization header.")
                .define("apiKey", "");

        COOLDOWN_SECONDS = builder
                .comment(
                        "Seconds between ordinary comments (join, etc.). " +
                                "Important events (death, advancement, dimension) ignore this. " +
                                "Chat has NO cooldown — replies as soon as Azure answers. " +
                                "Default 300 = 5 minutes.")
                .defineInRange("cooldownSeconds", 300, 5, 3600);

        REQUEST_TIMEOUT_SECONDS = builder
                .comment("HTTP timeout waiting for Python/Azure response (seconds).")
                .defineInRange("requestTimeoutSeconds", 60, 5, 120);

        CHAT_PREFIX = builder
                .comment("Chat name inside <> before the AI comment. Example: <Бог А> …")
                .define("chatPrefix", "Бог А");

        INBOUND_HTTP_ENABLED = builder
                .comment("Localhost HTTP for external agents (Claude MCP) to write to game chat.")
                .define("inboundHttpEnabled", true);

        INBOUND_HTTP_BIND = builder
                .comment("Bind address for inbound HTTP. Keep 127.0.0.1 — never expose publicly.")
                .define("inboundHttpBind", "127.0.0.1");

        INBOUND_HTTP_PORT = builder
                .comment("Port for inbound HTTP (POST /broadcast).")
                .defineInRange("inboundHttpPort", 8081, 1024, 65535);

        INBOUND_HTTP_API_KEY = builder
                .comment("Bearer token required by inbound HTTP. Empty = no auth (ok behind localhost).")
                .define("inboundHttpApiKey", "");

        builder.pop();
        SPEC = builder.build();
    }

    private ObserverConfig() {}
}
