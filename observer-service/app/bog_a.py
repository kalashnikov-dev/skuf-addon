"""
Bog A / AI Observer — инференс-чат в стиле Артура через Gemini API.

Клонирует стиль Артура из chat_output.txt (prompt engineering: system prompt +
style guide + few-shot примеры) и гоняет его через Gemini.

Использует OpenAI-совместимый эндпоинт Google AI Studio
(generativelanguage.googleapis.com/v1beta/openai/) — именно он доступен ключу,
нативный generateContent на этом проекте отдаёт 403.

Запуск:
    python bog_a.py
    python bog_a.py --model 3.1-flash-lite
    python bog_a.py --list-models --probe

Команды в чате:
    /model [ключ]   — сменить/выбрать модель (без аргумента — список)
    /models         — список моделей + что реально доступно ключу
    /reset          — очистить историю диалога
    /event <json>   — прогнать игровое событие через observer-режим (как в skuf-addon)
    /system         — показать текущий system prompt
    /stream         — тумблер стриминга ответа
    /temp <float>   — сменить temperature
    /help           — помощь
    /quit /exit     — выход

Ключ GEMINI_API_KEY берётся из .env рядом со скриптом.

Перспектива интеграции в kalashnikov-dev/skuf-addon → observer-service:
    from bog_a import BogA
    bog = BogA(model="3.1-flash-lite")
    comment = bog.observe(events=[...], online_players=[...])   # -> str | None
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("нет python-dotenv. поставь: pip install python-dotenv", file=sys.stderr)
    raise

try:
    from openai import OpenAI
except ImportError:
    print("нет openai. поставь: pip install openai", file=sys.stderr)
    raise


ROOT = Path(__file__).resolve().parent
PERSONA_DIR = ROOT / "persona"

GEMINI_OPENAI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai/"

# --- Реестр моделей ---------------------------------------------------------
# Ключ -> (человекочитаемое имя, id модели для OpenAI-эндпоинта, доступна_для_чата).
# Проверено 2026-07 на реальном ключе через OpenAI-совместимый эндпоинт.
MODELS: dict[str, tuple[str, str, bool]] = {
    # то что просил юзер
    "3.5-flash":       ("Gemini 3.5 Flash",      "gemini-3.5-flash",       True),
    "3.1-flash-lite":  ("Gemini 3.1 Flash Lite", "gemini-3.1-flash-lite",  True),
    "2.5-flash-lite":  ("Gemini 2.5 Flash Lite", "gemini-2.5-flash-lite",  True),
    # Antigravity через chat-completions НЕ работает: "only supports Interactions API".
    # Оставлен в реестре как явно недоступный, чтобы не путаться.
    "antigravity":     ("Antigravity",           "antigravity-preview-05-2026", False),
    # рабочие альтернативы
    "3-flash":         ("Gemini 3 Flash",        "gemini-3-flash-preview", True),
    "2.5-flash":       ("Gemini 2.5 Flash",      "gemini-2.5-flash",       True),
    "2.0-flash":       ("Gemini 2.0 Flash",      "gemini-2.0-flash",       True),
}
# Дефолт — 3.1 Flash Lite: реально доступна ключу и быстрая. 3.5-flash часто 503.
DEFAULT_MODEL = "3.1-flash-lite"

# Сколько few-shot примеров подкладывать по умолчанию.
# Замер на ключе: system+8fs -> 6/6 ok, +15fs -> 4/6, +30fs -> 0/6.
# Google модерит ВЕСЬ диалог: чем больше мата в контексте, тем чаще 403
# "project has been denied access" (у OpenAI-эндпоинта нет safetySettings).
# Держим 8 (надёжно проходит) и при контентном 403 разово откатываемся на 0
# (system-prompt в одиночку тоже отлично держит голос Артура).
# Ступени держим короткими — у моделей жёсткий лимит RPM (3.1-flash-lite = 15/мин),
# каждый лишний запрос жрёт квоту.
DEFAULT_FEWSHOTS = 8
FEWSHOT_FALLBACKS = [8, 0]  # ступени отката при контентном 403


def strip_html_tags_stream(chunks):
    """Стриминговый фильтр, удаляющий HTML-теги вроде <blockquote> на лету."""
    buffer = ""
    for chunk in chunks:
        buffer += chunk
        while True:
            idx = buffer.find('<')
            if idx == -1:
                yield buffer
                buffer = ""
                break
            if idx > 0:
                yield buffer[:idx]
                buffer = buffer[idx:]
                idx = 0
            close_idx = buffer.find('>')
            if close_idx == -1:
                if len(buffer) > 100:
                    yield buffer
                    buffer = ""
                break
            tag = buffer[:close_idx + 1]
            if re.match(r'^</?[a-zA-Z0-9]+(?:\s+[^>]*)?>$', tag):
                buffer = buffer[close_idx + 1:]
            else:
                yield buffer[0]
                buffer = buffer[1:]
    if buffer:
        yield buffer



def _load_persona(cag_lines: int = 1000) -> tuple[str, list[dict], dict, str]:
    system = (PERSONA_DIR / "system_prompt.txt").read_text(encoding="utf-8")
    fewshots = json.loads((PERSONA_DIR / "fewshots.json").read_text(encoding="utf-8"))
    style = json.loads((PERSONA_DIR / "style_guide.json").read_text(encoding="utf-8"))
    chat_path = ROOT / "chat_output.txt"
    chat_history = ""
    if chat_path.exists() and cag_lines > 0:
        lines = chat_path.read_text(encoding="utf-8").splitlines()
        chat_history = "\n".join(lines[-cag_lines:])
    return system, fewshots, style, chat_history



def _fewshot_messages(fewshots: list[dict]) -> list[dict]:
    """Few-shot примеры как история сообщений (user=setup, assistant=реплика Артура)."""
    msgs: list[dict] = []
    for ex in fewshots:
        msgs.append({"role": "user", "content": ex["setup"]})
        msgs.append({"role": "assistant", "content": ex["arthur"]})
    return msgs


class BogA:
    """Стейт чата: клиент, персона, история, выбранная модель."""

    def __init__(self, model: str = DEFAULT_MODEL, temperature: float = 1.15,
                 api_key: str | None = None, n_fewshots: int = DEFAULT_FEWSHOTS,
                 cag_lines: int = 1000):
        load_dotenv(ROOT / ".env", override=True)
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise SystemExit("нет GEMINI_API_KEY в .env")
        self.client = OpenAI(api_key=key, base_url=GEMINI_OPENAI_BASE)
        system_base, self.fewshots, self.style, raw_chat = _load_persona(cag_lines)
        self.system = system_base
        
        # 1. Load facts.txt if it exists (CAG optimized database)
        facts_path = PERSONA_DIR / "facts.txt"
        if facts_path.exists():
            print(f"[CAG] Loading pre-compiled facts database from {facts_path}")
            facts_text = facts_path.read_text(encoding="utf-8")
            self.system += f"\n\n# БАЗА ФАКТОВ О ГРУППЕ ДРУЗЕЙ (ТВОИ ЗНАНИЯ):\n{facts_text}"
            # If facts are loaded, we only need a small slice of raw chat (e.g. 150 lines) to serve as a style guide
            if raw_chat:
                lines = raw_chat.splitlines()
                raw_chat = "\n".join(lines[-min(cag_lines, 150):])
        
        # 2. Append raw chat as a style guide template
        if raw_chat:
            self.system += (
                "\n\n# ШАБЛОН СТИЛЯ И ПОСЛЕДНЯЯ ПЕРЕПИСКА (ПИШИ ТОЧНО В ТАКОМ ЖЕ СТИЛЕ И ФОРМАТЕ):\n"
                "<chat_history>\n"
                f"{raw_chat}\n"
                "</chat_history>\n"
            )
        self._all_fewshot_msgs = _fewshot_messages(self.fewshots)
        self.n_fewshots = n_fewshots      # сколько примеров подкладываем
        self.history: list[dict] = []      # живой диалог поверх few-shot
        self.temperature = temperature
        # Станет True, если деплой отверг reasoning_effort — тогда шлём без него
        self._reasoning_unsupported = False
        self.set_model(model)

    # --- модель ---
    def set_model(self, key: str) -> str:
        """Ключ из MODELS или сырой id деплоя (Azure Foundry: gpt-5-mini и т.п.)."""
        if key in MODELS:
            self.model_key = key
            self.model_name, self.model_id, self.model_ok = MODELS[key]
            return self.model_id
        # Passthrough для Azure/другого OpenAI-compatible деплоя
        if not key or not str(key).strip():
            raise KeyError(key)
        self.model_key = key
        self.model_name = key
        self.model_id = key
        self.model_ok = True
        return self.model_id

    def _messages(self, tail: list[dict], n_fewshots: int | None = None) -> list[dict]:
        n = self.n_fewshots if n_fewshots is None else n_fewshots
        few = self._all_fewshot_msgs[: n * 2]  # по 2 сообщения на пример
        return [{"role": "system", "content": self.system}] + few + tail

    @staticmethod
    def _is_content_403(e: Exception) -> bool:
        s = str(e)
        return "403" in s and "denied access" in s.lower()

    @staticmethod
    def _is_transient(e: Exception) -> bool:
        s = str(e).lower()
        return any(t in s for t in ("429", "503", "rate limit", "overloaded"))

    @staticmethod
    def _is_reasoning_param_error(e: Exception) -> bool:
        """Деплой не знает про reasoning_effort (400 unknown/unsupported parameter)."""
        s = str(e).lower()
        return "reasoning_effort" in s or (
            "reasoning" in s and ("unsupported" in s or "unknown" in s or "unexpected" in s)
        )

    @staticmethod
    def _retry_delay(e: Exception, default: float) -> float:
        """Достаёт 'retryDelay': '18s' из тела 429, иначе default."""
        m = re.search(r"retry(?:Delay|.{0,4}in)['\":\s]+(\d+(?:\.\d+)?)s", str(e))
        if m:
            return min(float(m.group(1)) + 0.5, 30.0)
        return default

    def _uses_max_completion_tokens(self) -> bool:
        mid = (self.model_id or "").lower()
        return mid.startswith("gpt-5") or "gpt-5" in mid

    def _complete(self, tail: list[dict], max_tokens: int = 400,
                  retries: int = 3) -> str:
        """
        Запрос с бэкоффом на временные ошибки (429/503) И деградацией few-shot
        на контентном 403 (Google модерит весь диалог; урезаем примеры пока не пройдёт).
        """
        last: Exception | None = None
        for fs in FEWSHOT_FALLBACKS:
            if fs > self.n_fewshots:
                continue
            messages = self._messages(tail, n_fewshots=fs)
            for i in range(retries):
                try:
                    kwargs: dict = {
                        "model": self.model_id,
                        "messages": messages,
                    }
                    # gpt-5*: max_tokens часто даёт пустой content; temperature может быть запрещён.
                    # reasoning_effort=minimal — чтобы reasoning-токены не съедали весь бюджет
                    # и ответ не выходил пустым/сухим (главная причина «тупости» observer).
                    if self._uses_max_completion_tokens():
                        kwargs["max_completion_tokens"] = max(max_tokens, 800)
                        effort = os.environ.get("AZURE_REASONING_EFFORT", "minimal").strip()
                        if effort and not self._reasoning_unsupported:
                            kwargs["reasoning_effort"] = effort
                    else:
                        kwargs["temperature"] = self.temperature
                        kwargs["top_p"] = 0.95
                        kwargs["max_tokens"] = max_tokens
                    r = self.client.chat.completions.create(**kwargs)
                    raw_reply = (r.choices[0].message.content or "").strip()
                    return "".join(strip_html_tags_stream([raw_reply]))
                except Exception as e:  # noqa: BLE001
                    last = e
                    # Деплой не принимает reasoning_effort — запоминаем и повторяем без него
                    if not self._reasoning_unsupported and self._is_reasoning_param_error(e):
                        self._reasoning_unsupported = True
                        continue
                    if self._is_transient(e) and i < retries - 1:
                        time.sleep(self._retry_delay(e, default=2.0 * (2 ** i)))
                        continue
                    if self._is_content_403(e):
                        break  # урезаем few-shot и пробуем следующую ступень
                    raise
        raise last  # type: ignore[misc]

    def reset(self) -> None:
        self.history = []

    # --- обычный чат ---
    def say(self, user_text: str) -> str:
        """Одна реплика в диалоге. Держит контекст в self.history."""
        self.history.append({"role": "user", "content": user_text})
        reply = self._complete(self.history)
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def say_stream(self, user_text: str):
        """
        Генератор кусков ответа (стриминг). По завершении пишет в history.
        На контентном 403 стриминг не деградирует (нельзя «отмотать» уже
        выданные куски) — пробрасывает исключение, CLI откатится на say().
        """
        self.history.append({"role": "user", "content": user_text})
        messages = self._messages(self.history)

        def generate_raw():
            stream = self.client.chat.completions.create(
                model=self.model_id, messages=messages,
                temperature=self.temperature, top_p=0.95, max_tokens=400, stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        acc = ""
        for piece in strip_html_tags_stream(generate_raw()):
            acc += piece
            yield piece
        self.history.append({"role": "assistant", "content": acc.strip()})

    # --- observer-режим (совместим с skuf-addon/observer-service POST /events) ---
    def observe(self, events: list[dict], online_players: list[str] | None = None,
                memory_block: str | None = None) -> str | None:
        """
        Прогоняет игровые события через персону, возвращает реплику в чат или None
        (молчать). Формат events совпадает с payload observer-service:
        {event_id, timestamp, player, type, payload, dimension?, pos?}.

        memory_block (факты + недавняя история) кладётся в ХВОСТ user-промпта, а не
        в self.system — так статический префикс (persona+facts+fewshots) не меняется
        между вызовами и провайдер кэширует его автоматически (prompt caching).
        Сам вызов остаётся stateless: непрерывность даёт переданный memory_block.
        """
        if not events:
            return None
        lines = []
        if online_players:
            lines.append("в игре: " + ", ".join(online_players))
        for e in events:
            who = e.get("player", "кто-то")
            typ = e.get("type", "?")
            payload = e.get("payload", {})
            extra = f" ({json.dumps(payload, ensure_ascii=False)})" if payload else ""
            lines.append(f"{who} -> {typ}{extra}")

        prompt_parts = []
        if memory_block:
            prompt_parts.append(memory_block.strip())
        prompt_parts.append("события в игре:\n" + "\n".join(lines))
        prompt_parts.append(
            "кинь реплику в чат как артур (или пусто если не на что реагировать)"
        )
        prompt = "\n\n".join(prompt_parts)
        reply = self._complete([{"role": "user", "content": prompt}], max_tokens=200)
        return reply or None


# --- CLI --------------------------------------------------------------------
BANNER = r"""
  ___              _
 | _ ) ___  __ _  /_\
 | _ \/ _ \/ _` |/ _ \    AI Observer — стиль Артура
 |___/\___/\__, /_/ \_\   (skuf-addon / observer prototype)
           |___/
"""


def _probe_one(boga: BogA, model_id: str) -> str:
    try:
        boga.client.chat.completions.create(
            model=model_id, messages=[{"role": "user", "content": "привет"}],
            max_tokens=5,
        )
        return "[доступна]"
    except Exception as e:  # noqa: BLE001
        s = str(e)
        for code, tag in (("403", "403 нет доступа"), ("429", "429 квота"),
                          ("503", "503 занята"), ("404", "404 нет модели"),
                          ("400", "400 не chat-модель")):
            if code in s:
                return f"[{tag}]"
        return f"[{type(e).__name__}]"


def _print_models(boga: BogA, probe: bool = False) -> None:
    print("\nмодели (ключ -> имя / id):")
    for k, (name, mid, ok) in MODELS.items():
        mark = " *" if k == boga.model_key else "  "
        note = "" if ok else "  (не chat-модель)"
        line = f"{mark} {k:16} {name:24} {mid}{note}"
        if probe:
            line += "   " + _probe_one(boga, mid)
        print(line)
    print()


def _friendly_error(e: Exception) -> str:
    s = str(e)
    if "403" in s:
        return ("403: у проекта этого ключа нет доступа к модели. смени модель (/models).")
    if "429" in s:
        return "429: кончилась квота на эту модель. подожди или смени модель (/model)."
    if "503" in s:
        return "503: модель сейчас перегружена (Google-side). повтори позже или смени модель."
    if "400" in s and "Interactions" in s:
        return "400: эта модель не поддерживает chat-режим. выбери другую (/models)."
    return f"{type(e).__name__}: {s[:200]}"


def _render(text: str, raw: bool = False) -> str:
    if raw or not text:
        return text or "(тишина)"
    return "\n".join("  " + ln for ln in text.split("\n"))


def repl(boga: BogA) -> None:
    stream = True
    print(BANNER)
    print(f"модель: {boga.model_name} ({boga.model_id})  temp={boga.temperature}")
    if not boga.model_ok:
        print("! выбранная модель не поддерживает chat — переключись через /model")
    print("пиши сообщение. /help — команды. /quit — выход.\n")
    while True:
        try:
            line = input("ты> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nпока")
            return
        if not line:
            continue

        if line in ("/quit", "/exit", "/q"):
            print("пока")
            return
        if line == "/help":
            doc = __doc__ or ""
            print(textwrap.dedent(doc.split("Команды в чате:")[-1].split("Ключ")[0]))
            continue
        if line == "/reset":
            boga.reset()
            print("(история очищена)")
            continue
        if line == "/system":
            print("\n" + boga.system + "\n")
            continue
        if line == "/stream":
            stream = not stream
            print(f"(stream = {stream})")
            continue
        if line == "/models":
            print("(проверяю доступность, секунду...)")
            _print_models(boga, probe=True)
            continue
        if line.startswith("/temp"):
            try:
                boga.temperature = float(line.split(maxsplit=1)[1])
                print(f"(temp = {boga.temperature})")
            except (IndexError, ValueError):
                print("формат: /temp 1.1")
            continue
        if line.startswith("/model"):
            parts = line.split(maxsplit=1)
            if len(parts) == 1:
                _print_models(boga)
                continue
            key = parts[1].strip()
            try:
                boga.set_model(key)
                print(f"(модель: {boga.model_name} / {boga.model_id})")
                if not boga.model_ok:
                    print("! эта модель не chat — ответы не пойдут")
            except KeyError:
                print(f"нет такого ключа: {key}. смотри /models")
            continue
        if line.startswith("/event"):
            arg = line[len("/event"):].strip()
            try:
                data = json.loads(arg) if arg else {}
            except json.JSONDecodeError as e:
                print(f"кривой json: {e}")
                continue
            events = data.get("events", [data] if data else [])
            players = data.get("online_players")
            try:
                out = boga.observe(events, players)
                print("Bog A>")
                print(_render(out or "", False))
            except Exception as e:  # noqa: BLE001
                print("!", _friendly_error(e))
            continue

        # обычная реплика
        try:
            if stream:
                try:
                    print("Bog A>")
                    print("  ", end="", flush=True)
                    for piece in boga.say_stream(line):
                        print(piece.replace("\n", "\n  "), end="", flush=True)
                    print()
                except Exception as e:  # noqa: BLE001
                    # стриминг не умеет деградировать few-shot — откат на say()
                    if not BogA._is_content_403(e):
                        raise
                    if boga.history and boga.history[-1]["role"] == "user":
                        boga.history.pop()
                    print("\r  (модерация зарезала контекст, срезаю примеры...)")
                    reply = boga.say(line)
                    print("Bog A>")
                    print(_render(reply))
            else:
                reply = boga.say(line)
                print("Bog A>")
                print(_render(reply))
        except Exception as e:  # noqa: BLE001
            print("!", _friendly_error(e))
            if boga.history and boga.history[-1]["role"] == "user":
                boga.history.pop()


def main() -> None:
    ap = argparse.ArgumentParser(description="Bog A — инференс-чат в стиле Артура")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help=f"ключ модели (по умолчанию {DEFAULT_MODEL}). см. --list-models")
    ap.add_argument("--temp", type=float, default=1.15, help="temperature")
    ap.add_argument("--list-models", action="store_true", help="показать модели и выйти")
    ap.add_argument("--probe", action="store_true",
                    help="с --list-models: проверить доступность каждой модели")
    ap.add_argument("--cag-lines", type=int, default=1000,
                    help="сколько последних строк из chat_output.txt подкладывать в контекст (0 для отключения)")
    args = ap.parse_args()

    try:
        boga = BogA(model=args.model, temperature=args.temp, cag_lines=args.cag_lines)
    except KeyError:
        print(f"нет ключа модели '{args.model}'. доступные: {', '.join(MODELS)}")
        sys.exit(1)

    if args.list_models:
        _print_models(boga, probe=args.probe)
        return

    repl(boga)


if __name__ == "__main__":
    main()
