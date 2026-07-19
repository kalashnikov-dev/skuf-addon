package com.arturgpt.skufaddon.observer;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.regex.Pattern;

/**
 * Детектор обращения к наблюдателю в чате.
 *
 * Алиасы без учёта регистра. Многословные («бог а») и длинные проверяются первыми.
 * Одиночная «А» — только если похоже на обращение, а не союз «а я / а потом».
 */
public final class ObserverChatMentions {

    /** Союз «а …» в начале фразы — не обращение к Богу А. */
    private static final Pattern A_CONJUNCTION = Pattern.compile(
            "(?U)^а\\s+(я|ты|он|она|мы|вы|они|потом|то|ну|вот|ещё|еще|как|что|это|если|раз|мне|тебе)\\b");

    private ObserverChatMentions() {}

    /**
     * @return сработавший алиас в нижнем регистре, или null если не обращение
     */
    public static String findMention(String rawMessage) {
        if (rawMessage == null || rawMessage.isBlank()) {
            return null;
        }

        String normalized = normalize(rawMessage);
        List<String> aliases = aliasesLongestFirst();

        for (String alias : aliases) {
            if (alias.isEmpty()) {
                continue;
            }
            if (alias.equals("а")) {
                if (matchesLetterA(normalized)) {
                    return alias;
                }
                continue;
            }
            if (containsAlias(normalized, alias)) {
                return alias;
            }
        }
        return null;
    }

    public static boolean isAddressed(String rawMessage) {
        return findMention(rawMessage) != null;
    }

    private static List<String> aliasesLongestFirst() {
        List<? extends String> configured = ObserverConfig.CHAT_ALIASES.get();
        List<String> out = new ArrayList<>();
        if (configured != null) {
            for (String a : configured) {
                if (a != null && !a.isBlank()) {
                    out.add(normalize(a));
                }
            }
        }
        out.sort(Comparator.comparingInt(String::length).reversed());
        return out;
    }

    /** lower + схлопнуть пробелы */
    static String normalize(String s) {
        String lower = s.toLowerCase(Locale.ROOT).trim();
        return lower.replaceAll("\\s+", " ");
    }

    /**
     * Фраза или слово целиком (границы по буквам/цифрам, кириллица ок).
     */
    static boolean containsAlias(String normalizedMessage, String alias) {
        String quoted = Pattern.quote(alias);
        // (?U) = Unicode-aware; не буква/цифра/_ вокруг алиаса
        Pattern p = Pattern.compile("(?U)(?<![\\p{L}\\p{N}_])" + quoted + "(?![\\p{L}\\p{N}_])");
        return p.matcher(normalizedMessage).find();
    }

    /**
     * «А» как обращение: @а, «А, …» / «А: …», «эй А», «А?» в конце,
     * или «А помоги…» в начале, но не союз «а я / а потом».
     */
    static boolean matchesLetterA(String normalized) {
        if (normalized.contains("@а")) {
            // @а как токен
            if (Pattern.compile("(?U)(^|\\s)@а(?![\\p{L}\\p{N}_])").matcher(normalized).find()) {
                return true;
            }
        }
        // А, … / А: … / А! …
        if (Pattern.compile("(?U)^а\\s*[,:!]").matcher(normalized).find()) {
            return true;
        }
        // … А? / … А!
        if (Pattern.compile("(?U)(^|[\\s,])а\\s*[?!]+$").matcher(normalized).find()) {
            return true;
        }
        // эй А / эй, А
        if (Pattern.compile("(?U)\\bэй\\s*,?\\s*а(?![\\p{L}\\p{N}_])").matcher(normalized).find()) {
            return true;
        }
        // «А помоги» в начале, но отсекаем типичный союз
        if (normalized.startsWith("а ") && !A_CONJUNCTION.matcher(normalized).find()) {
            return true;
        }
        return false;
    }
}
