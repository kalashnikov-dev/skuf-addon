# Skuf Observer Service

Маленький Python-сервис рядом с Minecraft: принимает игровые события и возвращает текст комментария для чата.

Сейчас это **заглушка** (без Azure). Нужна, чтобы проверить связь «мод → сервис → ответ».

## Требования

- Python 3.10+ (лучше 3.11/3.12)
- (позже) Docker — когда будем выкладывать на VPS

## Быстрый старт (локально)

```powershell
cd observer-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Проверки:

- Health: http://127.0.0.1:8080/health → `{"status":"ok"}`
- Документация / тест запросов: http://127.0.0.1:8080/docs
- `POST /events` — тело с `events` и `online_players`, ответ `{ "comment": "..." }` или `null`

## Azure / Microsoft Foundry

У Foundry-проекта нужен **не** классический `*.openai.azure.com`, а URL вида:

`https://....services.ai.azure.com/api/projects/..../openai/v1`

В коде используется `OpenAI(base_url=..., api_key=...)`, как в рабочем скрипте из консольки.

1. Скопируй `.env.example` → `.env`
2. Вставь тот же endpoint/key/deployment, что уже работали у тебя локально
3. `pip install -r requirements.txt`
4. Перезапусти uvicorn → `/health` должен показать `"azure_configured": true`


Мод шлёт:

```json
{
  "events": [
    {
      "event_id": "…",
      "timestamp": 1710000000,
      "player": "Nick",
      "type": "death",
      "payload": {},
      "dimension": "minecraft:overworld",
      "pos": [0, 64, 0]
    }
  ],
  "online_players": ["Nick"]
}
```

Сервис отвечает:

```json
{ "comment": "текст для чата" }
```

или `{ "comment": null }`, если молчать.
