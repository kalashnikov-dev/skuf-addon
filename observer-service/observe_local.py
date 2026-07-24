#!/usr/bin/env python3
"""
Harness для локального тестирования ИИ-наблюдателя «Бог А» (skuf-addon / observer-service).

Запускает реальный FastAPI app in-process через Starlette TestClient,
прогоняя запросы через ВСЮ серверную логику (lifespan, провайдер, RAG-память,
«запомни», asyncio.to_thread, фоновые факты).

Примеры использования:
    # 1. Интерактивный REPL (дефолт):
    python observe_local.py

    # 2. REPL с определенным игроком и списком онлайн:
    python observe_local.py --player Steve --online Steve,Alex

    # 3. Автоматический сценарный прогон с паузой между шагами:
    python observe_local.py --scenario scenarios/demo.json --delay 2 --dump-memory

    # 4. Прогон с использованием реального серверного каталога памяти:
    python observe_local.py --memory-dir ./data
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import builtins
import sys
import uuid
from pathlib import Path
from typing import Any

_orig_print = builtins.print


def safe_print(*args, **kwargs) -> None:
    try:
        _orig_print(*args, **kwargs)
    except UnicodeEncodeError:
        msg = " ".join(str(a) for a in args)
        enc = sys.stdout.encoding or "utf-8"
        _orig_print(msg.encode(enc, errors="replace").decode(enc), **kwargs)


print = safe_print


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Локальный harness для тестирования Бог А в observer-service."
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Путь к JSON-файлу сценария (если задан — выполняется сценарий вместо REPL).",
    )
    parser.add_argument(
        "--player",
        type=str,
        default="tester",
        help="Имя стартового игрока (дефолт: tester).",
    )
    parser.add_argument(
        "--online",
        type=str,
        default=None,
        help="Список онлайн-игроков через запятую (например: tester,arsen).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Задержка в секундах между шагами в сценарном режиме (дефолт: 0).",
    )
    parser.add_argument(
        "--dump-memory",
        action="store_true",
        help="Дамп содержимого памяти (GET /memory) по завершении сценария.",
    )
    parser.add_argument(
        "--memory-dir",
        type=str,
        default="./data-local",
        help="Каталог памяти (по умолчанию ./data-local для изоляции от прод-данных).",
    )
    return parser.parse_args()


# Важно: устанавливаем MEMORY_DIR ДО импорта app.main
args = _parse_args()
os.environ["MEMORY_DIR"] = args.memory_dir

try:
    from starlette.testclient import TestClient
except ImportError:
    print("Ошибка: httpx не установлен. Установи: pip install httpx", file=sys.stderr)
    sys.exit(1)

from app.main import app  # noqa: E402


def build_event(
    player: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
    dimension: str | None = None,
    pos: list[int] | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    return {
        "event_id": event_id or str(uuid.uuid4()),
        "timestamp": time.time(),
        "player": player,
        "type": event_type,
        "payload": payload or {},
        "dimension": dimension,
        "pos": pos,
    }


def send_events_request(
    client: TestClient, events: list[dict[str, Any]], online_players: list[str]
) -> tuple[str | None, float]:
    start_time = time.perf_counter()
    response = client.post(
        "/events",
        json={"events": events, "online_players": online_players},
    )
    elapsed = time.perf_counter() - start_time

    if response.status_code != 200:
        print(f"[!] HTTP error {response.status_code}: {response.text}")
        return None, elapsed

    data = response.json()
    return data.get("comment"), elapsed


def print_health(client: TestClient) -> None:
    res = client.get("/health")
    print("\n--- GET /health ---")
    print(json.dumps(res.json(), indent=2, ensure_ascii=False))
    print("-------------------\n")


def print_memory(client: TestClient, limit: int = 20) -> None:
    res = client.get(f"/memory?limit={limit}")
    print(f"\n--- GET /memory (limit={limit}) ---")
    print(json.dumps(res.json(), indent=2, ensure_ascii=False))
    print("--------------------\n")


def run_scenario(client: TestClient, scenario_path: str, default_player: str, default_online: list[str], delay: float, dump_mem: bool) -> None:
    path = Path(scenario_path)
    if not path.exists():
        print(f"[!] Файл сценария не найден: {scenario_path}", file=sys.stderr)
        sys.exit(1)

    try:
        scenario_data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[!] Ошибка чтения JSON сценария: {exc}", file=sys.stderr)
        sys.exit(1)

    online_players: list[str] = scenario_data.get("online_players", default_online)
    steps: list[dict[str, Any]] = scenario_data.get("steps", [])

    print(f"\n=== Запуск сценария: {scenario_path} ({len(steps)} шагов) ===")
    print(f"Онлайн-игроки: {', '.join(online_players)}")
    print("=" * 50)

    replies_count = 0
    skip_count = 0

    for i, step in enumerate(steps, 1):
        # Поддержка короткой формы {"chat": "...", "player": "..."} или полного объекта события
        if "chat" in step:
            player = step.get("player", default_player)
            event = build_event(player, "chat", payload={"message": step["chat"]})
        elif "type" in step:
            player = step.get("player", default_player)
            event = build_event(
                player=player,
                event_type=step["type"],
                payload=step.get("payload"),
                dimension=step.get("dimension"),
                pos=step.get("pos"),
                event_id=step.get("event_id"),
            )
        elif "events" in step:
            # Шаг содержит сразу массив событий
            raw_events = step["events"]
            events_to_send = []
            for rev in raw_events:
                events_to_send.append(
                    build_event(
                        player=rev.get("player", default_player),
                        event_type=rev.get("type", "chat"),
                        payload=rev.get("payload"),
                        dimension=rev.get("dimension"),
                        pos=rev.get("pos"),
                    )
                )
            event_summary = f"batch({len(events_to_send)} events)"
            comment, elapsed = send_events_request(client, events_to_send, online_players)
            if comment:
                replies_count += 1
                print(f"Шаг {i}/{len(steps)} [{event_summary}] ({elapsed:.2f}s) -> <Бог А> {comment}")
            else:
                skip_count += 1
                print(f"Шаг {i}/{len(steps)} [{event_summary}] ({elapsed:.2f}s) -> (молчит / SKIP)")
            if delay > 0 and i < len(steps):
                time.sleep(delay)
            continue
        else:
            # Неизвестный формат шага
            event = step

        event_desc = f"{event['player']}:{event['type']}"
        if event["type"] == "chat":
            event_desc += f" ('{event.get('payload', {}).get('message', '')}')"

        comment, elapsed = send_events_request(client, [event], online_players)
        if comment:
            replies_count += 1
            print(f"Шаг {i}/{len(steps)} [{event_desc}] ({elapsed:.2f}s) -> <Бог А> {comment}")
        else:
            skip_count += 1
            print(f"Шаг {i}/{len(steps)} [{event_desc}] ({elapsed:.2f}s) -> (молчит / SKIP)")

        if delay > 0 and i < len(steps):
            time.sleep(delay)

    print("=" * 50)
    print(f"Сценарий завершён! Всего шагов: {len(steps)}, Ответов: {replies_count}, Молний/SKIP: {skip_count}")

    if dump_mem:
        print_memory(client)


def run_repl(client: TestClient, initial_player: str, initial_online: list[str]) -> None:
    current_player = initial_player
    online_players = list(initial_online)
    if current_player not in online_players:
        online_players.append(current_player)

    print("\n" + "=" * 60)
    print("  ИИ-Наблюдатель «Бог А» — Интерактивный локальный harness")
    print("=" * 60)
    print(f"Игрок: {current_player}")
    print(f"Онлайн: {', '.join(online_players)}")
    print(f"Память: {os.environ.get('MEMORY_DIR')}")
    print("\nВведи текст сообщения для чата или команду (/help для списка).")
    print("-" * 60 + "\n")

    while True:
        try:
            user_input = input(f"[{current_player}] > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nВыход.")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd in ("/quit", "/exit"):
                print("Выход.")
                break

            elif cmd == "/help":
                print("\nКоманды harness:")
                print("  /player <ник>      — сменить текущего игрока")
                print("  /players [a,b,c]   — показать или задать список онлайн-игроков")
                print("  /join [ник]        — событие join (добавляет в онлайн)")
                print("  /leave [nick]      — обновить онлайн (мод leave как /events не шлёт)")
                print("  /death [причина]   — событие смерти игрока")
                print("  /adv <название>    — событие достижения (advancement)")
                print("  /dim <from> <to>   — событие смены измерения")
                print("  /event <json>      — сырое событие в формате JSON")
                print("  /health            — проверить статус сервера (GET /health)")
                print("  /memory [limit]    — дамп памяти Бог А (GET /memory)")
                print("  /help              — эта справка")
                print("  /quit, /exit       — завершить работу\n")
                continue

            elif cmd == "/player":
                if not arg:
                    print(f"Текущий игрок: {current_player}")
                else:
                    current_player = arg
                    if current_player not in online_players:
                        online_players.append(current_player)
                    print(f"Текущий игрок изменён на: {current_player}")
                continue

            elif cmd == "/players":
                if arg:
                    online_players = [p.strip() for p in arg.split(",") if p.strip()]
                    if current_player not in online_players:
                        online_players.append(current_player)
                    print(f"Онлайн-игроки обновлены: {', '.join(online_players)}")
                else:
                    print(f"Онлайн-игроки: {', '.join(online_players)}")
                continue

            elif cmd == "/join":
                target_player = arg if arg else current_player
                if target_player not in online_players:
                    online_players.append(target_player)
                ev = build_event(target_player, "join")
                comment, elapsed = send_events_request(client, [ev], online_players)
                if comment:
                    print(f"<Бог А> {comment} ({elapsed:.2f}s)")
                else:
                    print(f"(молчит / SKIP) ({elapsed:.2f}s)")
                continue

            elif cmd == "/leave":
                target_player = arg if arg else current_player
                if target_player in online_players:
                    online_players.remove(target_player)
                print(f"Игрок {target_player} вышел из онлайна. Текущий онлайн: {', '.join(online_players)}")
                continue

            elif cmd == "/death":
                cause = arg or "died mysteriously"
                ev = build_event(current_player, "death", payload={"death_message": cause, "cause": cause})
                comment, elapsed = send_events_request(client, [ev], online_players)
                if comment:
                    print(f"<Бог А> {comment} ({elapsed:.2f}s)")
                else:
                    print(f"(молчит / SKIP) ({elapsed:.2f}s)")
                continue

            elif cmd == "/adv":
                if not arg:
                    print("Использование: /adv <название достижения>")
                    continue
                ev = build_event(current_player, "advancement", payload={"title": arg, "advancement": arg})
                comment, elapsed = send_events_request(client, [ev], online_players)
                if comment:
                    print(f"<Бог А> {comment} ({elapsed:.2f}s)")
                else:
                    print(f"(молчит / SKIP) ({elapsed:.2f}s)")
                continue

            elif cmd == "/dim":
                bits = arg.split()
                from_dim = bits[0] if len(bits) > 0 else "minecraft:overworld"
                to_dim = bits[1] if len(bits) > 1 else "minecraft:the_nether"
                ev = build_event(
                    current_player,
                    "dimension",
                    payload={"from": from_dim, "to": to_dim},
                    dimension=to_dim,
                )
                comment, elapsed = send_events_request(client, [ev], online_players)
                if comment:
                    print(f"<Бог А> {comment} ({elapsed:.2f}s)")
                else:
                    print(f"(молчит / SKIP) ({elapsed:.2f}s)")
                continue

            elif cmd == "/event":
                if not arg:
                    print("Использование: /event <json>")
                    continue
                try:
                    data = json.loads(arg)
                    if isinstance(data, dict):
                        events = [data]
                    elif isinstance(data, list):
                        events = data
                    else:
                        print("[!] Неверный JSON")
                        continue
                    comment, elapsed = send_events_request(client, events, online_players)
                    if comment:
                        print(f"<Бог А> {comment} ({elapsed:.2f}s)")
                    else:
                        print(f"(молчит / SKIP) ({elapsed:.2f}s)")
                except Exception as exc:
                    print(f"[!] Ошибка парсинга JSON: {exc}")
                continue

            elif cmd == "/health":
                print_health(client)
                continue

            elif cmd == "/memory":
                limit = int(arg) if arg.isdigit() else 20
                print_memory(client, limit=limit)
                continue

            else:
                print(f"Неизвестная команда {cmd}. Для справки введи /help")
                continue

        # Сообщение в чат от current_player
        ev = build_event(current_player, "chat", payload={"message": user_input})
        comment, elapsed = send_events_request(client, [ev], online_players)
        if comment:
            print(f"<Бог А> {comment} ({elapsed:.2f}s)")
        else:
            print(f"(молчит / SKIP) ({elapsed:.2f}s)")


def main() -> None:
    online_list = [p.strip() for p in args.online.split(",")] if args.online else [args.player]
    if args.player not in online_list:
        online_list.append(args.player)

    with TestClient(app) as client:
        if args.scenario:
            run_scenario(
                client=client,
                scenario_path=args.scenario,
                default_player=args.player,
                default_online=online_list,
                delay=args.delay,
                dump_mem=args.dump_memory,
            )
        else:
            run_repl(
                client=client,
                initial_player=args.player,
                initial_online=online_list,
            )


if __name__ == "__main__":
    main()
