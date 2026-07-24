# Claude / друг → Minecraft chat + Бог А (через SSH-туннель + MCP)

Целевое состояние: Claude на Windows ходит в observer на VM **только через SSH-туннель**
(8080 не торчит в интернет). Интерфейс — MCP (`/mcp`) + debug REST (`/chat`, `/logs`, `/send_chat`).

## 0. Рестриктнутый SSH-ключ для друга

Отдельный ключ: **только port-forward**, без shell / scp / agent.

### На машине друга (Windows)

```powershell
ssh-keygen -t ed25519 -f $env:USERPROFILE\.ssh\skuf_mcp_friend -C "friend-mcp-tunnel"
# приватный: ~/.ssh/skuf_mcp_friend
# публичный:  ~/.ssh/skuf_mcp_friend.pub  ← прислать тебе
```

### На VM (ты, один раз)

Скрипт в репо: `deploy/setup-friend-ssh.sh` — или вручную в `~/.ssh/authorized_keys`:

```
restrict,port-forwarding,permitopen="127.0.0.1:8080",permitopen="127.0.0.1:25575",command="/bin/false" ssh-ed25519 AAAA... friend-mcp-tunnel
```

- `restrict` — режет pty/X11/agent и т.п.
- `port-forwarding` + `permitopen` — разрешает **только** туннель на observer и (опционально) RCON
- `command="/bin/false"` — интерактивный shell не открывается

Проверка с Windows друга:

```powershell
ssh -i $env:USERPROFILE\.ssh\skuf_mcp_friend -N -L 8080:localhost:8080 dayntypou@35.246.234.79
# в другом окне:
curl http://localhost:8080/health
```

Ожидаемо: `ssh` без `-L` / попытка shell — сразу отвал; `/health` через туннель — JSON.

Персистентный туннель (позже): Task Scheduler + `ServerAliveInterval=30` `ServerAliveCountMax=3`.

## 1. Env на VM (`observer-service/.env`)

```
DEBUG_ENDPOINTS=true
DEBUG_API_KEY=          # лучше задать shared secret
SEND_CHAT_BACKEND=rcon  # или mod после деплоя jar
RCON_PASSWORD=...       # если rcon
RCON_HOST=host.docker.internal
```

После пуша `observer-service/**` автодеплой сам пересоберёт контейнер.

## 2. RCON (быстрый send_chat)

В `server.properties` на pack-сервере:

```
enable-rcon=true
rcon.port=25575
rcon.password=<тот же что RCON_PASSWORD>
# bind по возможности localhost-only (зависит от версии / флагов)
```

**Не** открывай 25575 в GCP firewall наружу — только через SSH `permitopen` или localhost с VM.

Переключение на мод (чище):

```
SEND_CHAT_BACKEND=mod
MOD_CHAT_URL=http://host.docker.internal:8081/broadcast
```

В `config/skufaddon-observer.toml`: `inboundHttpEnabled=true`, bind `127.0.0.1`, port `8081`.

## 3. REST (через туннель)

```powershell
curl http://localhost:8080/health
curl -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d "{\"message\":\"привет\"}"
curl "http://localhost:8080/logs?limit=50"
curl -X POST http://localhost:8080/send_chat -H "Content-Type: application/json" -d "{\"text\":\"всем привет\"}"
```

Если задан `DEBUG_API_KEY` — добавь `-H "Authorization: Bearer …"`.

## 4. MCP в Claude Code / Cursor

URL (локально через туннель): `http://localhost:8080/mcp`

Инструменты:

| tool | что делает |
|------|------------|
| `health` | статус observer / Бог А |
| `read_chat` | недавний чат/события из памяти |
| `read_memory` | факты + recent |
| `say_to_boga` | прямой разговор с Бог А (persist=false по умолч.) |
| `send_chat` | в игровой чат (RCON или мод) |
| `read_logs` | хвост логов sidecar |

Пример mcp.json (Claude Code):

```json
{
  "mcpServers": {
    "skuf-observer": {
      "type": "http",
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

(точный формат конфига зависит от клиента — главное URL `/mcp` за живым туннелем.)

## 5. Порядок проверки

1. Туннель + `/health`
2. `POST /chat` → реплика Бог А
3. MCP `read_chat` / `say_to_boga`
4. RCON `send_chat` → видно в игре
5. После деплоя jar: `SEND_CHAT_BACKEND=mod` → inbound `:8081`
