package com.arturgpt.skufaddon.observer;

import net.minecraftforge.common.ForgeConfigSpec;

import java.util.List;

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
     * Важные события (death, chat-mention) этот лимит игнорируют.
     * 300 = примерно раз в 5 минут.
     */
    public static final ForgeConfigSpec.IntValue COOLDOWN_SECONDS;

    public static final ForgeConfigSpec.IntValue REQUEST_TIMEOUT_SECONDS;

    /** Префикс в чате, например «Бог А» → сообщение вида «[Бог А] …». */
    public static final ForgeConfigSpec.ConfigValue<String> CHAT_PREFIX;

    /**
     * Как к наблюдателю обращаются в чате (регистр не важен).
     * Сообщение с любым из этих слов/фраз → событие chat и ответ ИИ.
     */
    public static final ForgeConfigSpec.ConfigValue<List<? extends String>> CHAT_ALIASES;

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
                                "Important events (death, chat mention) ignore this. Default 300 = 5 minutes.")
                .defineInRange("cooldownSeconds", 300, 5, 3600);

        REQUEST_TIMEOUT_SECONDS = builder
                .comment("HTTP timeout waiting for Python/Azure response (seconds).")
                .defineInRange("requestTimeoutSeconds", 60, 5, 120);

        CHAT_PREFIX = builder
                .comment("Chat name inside <> before the AI comment. Example: <Бог А> …")
                .define("chatPrefix", "Бог А");

        CHAT_ALIASES = builder
                .comment(
                        "Chat aliases that address the observer (case-insensitive). " +
                                "Single letter «А» only matches address-like uses, not conjunction «а я».")
                .defineList(
                        "chatAliases",
                        List.of("Бог А", "бог", "Артур", "Арт", "А"),
                        o -> o instanceof String);

        builder.pop();
        SPEC = builder.build();
    }

    private ObserverConfig() {}
}
