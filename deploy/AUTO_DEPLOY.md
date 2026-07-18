# Автодеплой с GitHub на GCP VM

После настройки: `git push origin main` сам обновит мод и/или Бог А на сервере.

## Как это работает

```
git push → GitHub Actions
           ├─ изменился src/     → ./gradlew build → scp jar → stop/start Minecraft
           └─ изменился observer → rsync кода → docker compose up --build
```

`.env` с ключами Azure **остаётся только на VM**, Actions его не заливает.

## Один раз: SSH-ключ

### На своём ПК (PowerShell)

```powershell
ssh-keygen -t ed25519 -C "github-deploy-skuf" -f "$env:USERPROFILE\.ssh\skuf_deploy" -N ""
```

Появятся:

- `skuf_deploy` — **приватный** (в GitHub Secret)
- `skuf_deploy.pub` — **публичный** (на VM)

### На VM (SSH в браузере)

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
# вставь ОДНУ строку из skuf_deploy.pub, сохрани
chmod 600 ~/.ssh/authorized_keys
```

Проверка с ПК:

```powershell
ssh -i $env:USERPROFILE\.ssh\skuf_deploy dayntypou@35.246.234.79
```

(подставь свой user/IP)

### GitHub → Settings → Secrets and variables → Actions → New repository secret

| Secret | Значение |
|---|---|
| `GCP_HOST` | `35.246.234.79` (External IP; если сменится после Stop/Start — обнови) |
| `GCP_USER` | `dayntypou` |
| `GCP_SSH_KEY` | весь текст файла `skuf_deploy` (включая `BEGIN`/`END`) |

## Один раз: структура на VM

Уже должно быть:

- `~/GregTech-Modern-Community-Pack/serverpack/` — Minecraft  
- `~/skuf-ai/observer-service/` + `~/skuf-ai/deploy/` — Docker observer + `.env`

Скрипт:

```bash
chmod +x ~/skuf-ai/deploy/remote-update.sh
```

(после первого успешного Actions он обновится сам)

## Ручной запуск

GitHub → Actions → **Deploy to GCP** → Run workflow  
Можно выбрать только мод или только observer.

## Важно

- Деплой мода **рестартит сервер** — вас кикнет на ~1–2 минуты.
- Меняешь только `README` / доки без `src` и `observer-service` — деплой **не** стартует.
- IP VM лучше сделать **статическим** (Reserve external IP), иначе после Stop секрет `GCP_HOST` устареет.
