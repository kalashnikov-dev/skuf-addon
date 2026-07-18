# Деплой: GregTech CEu Modern Community Pack + Skuf Addon + Бог А на Google Cloud

Для двоих игроков. Бюджет: пробные **~$250–300** Google Cloud (обычно на 90 дней).

## Что ставим (итоговая схема)

```
Google Cloud VM (Ubuntu 22.04)
├── Minecraft Forge 1.20.1
│   └── GregTech CEu Modern Community Pack (serverpack)
│       └── mods/skufaddon-....jar   ← наш аддон
├── Docker
│   └── observer-service (Python) на 127.0.0.1:8080
│       └── Azure/Foundry gpt-5-mini
└── Firewall
    ├── TCP 25565  ← открыт в интернет (Minecraft)
    └── TCP 8080   ← НЕ открываем (только localhost)
```

Клиенты: CurseForge / Prism — **клиентский** пак той же версии + jar аддона (или через модлист).

## Рекомендованная VM (зафиксировано)

| Параметр | Значение | Почему |
|---|---|---|
| Тип | **`e2-standard-4`** | 4 vCPU / **16 GB RAM** — комфорт для GT + 2 игрока + запас |
| Диск | **80 GB SSD** (Balanced) | моды + мир + бэкапы |
| ОС | **Ubuntu 22.04 LTS** | Java 17 из apt, стабильно |
| Регион | ближе к вам | `europe-west1` (Бельгия) / `europe-west2` (Лондон) / `europe-west3` (Франкфурт) |

Альтернатива подешевле: `e2-standard-2` (8 GB) — для ранней игры двоим часто хватает, на поздней GT может упираться в RAM.

Оценка: `e2-standard-4` ≈ **$70–110/мес** в Европе → **$250 хватит на ~2–3 месяца** 24/7. Чтобы растянуть кредит: выключай VM, когда не играете (`STOP`, не DELETE).

**Always Free `e2-micro` для этого пака не годится** (слишком мало RAM).

## Пак

- Клиент: [GregTech Community Pack Modern](https://www.curseforge.com/minecraft/modpacks/gregtech-community-pack-modern) (1.20.1 Forge)
- Сервер: на той же странице Files → **Server Pack** (`serverpack.zip`), сейчас линейка **1.14.x**
- Официальный репо: [GregTech-Modern-Community-Pack](https://github.com/GregTechCEu/GregTech-Modern-Community-Pack) — есть `serverpack/start.sh`

Версия GTCEu в аддоне: **7.5.1** (`gradle.properties`). Серверный пак лучше взять **не новее**, чем совместим с вашим jar, или обновить аддон под версию пака.

## Пошагово (ты в консоли GCP, я подскажу по SSH)

### 0. Аккаунт

1. https://console.cloud.google.com → войти Google-аккаунтом  
2. Активировать **Free Trial** ($300 / обычно 90 дней; карта нужна для верификации, списаний без явного апгрейда быть не должно — читай актуальный текст на экране)  
3. Создать проект, например `skuf-gt-server`

### 1. Firewall (до или сразу после VM)

**VPC network → Firewall → Create rule**

Правило Minecraft:

- Name: `allow-minecraft`
- Targets: All instances in the network (или tag `minecraft`)
- Source IP ranges: `0.0.0.0/0`
- Protocols/ports: **TCP 25565**

Правило SSH обычно уже есть (`default-allow-ssh`).

**Не открывай 8080.**

### 2. Создать VM

**Compute Engine → VM instances → Create**

- Name: `skuf-gt`
- Region/Zone: ближайший к вам
- Machine: **e2-standard-4**
- Boot disk: Ubuntu 22.04, **80 GB**, Balanced SSD
- Firewall: Allow HTTP/HTTPS **не обязательны** для MC
- Network tags (если используешь): `minecraft`

Создать → дождаться External IP (например `34.x.x.x`).

### 3. SSH

В строке VM нажать **SSH** (браузер) или локально:

```bash
gcloud compute ssh skuf-gt --zone=ТВОЯ_ЗОНА
```

### 4. Базовая установка на VM

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y openjdk-17-jre-headless unzip curl git screen docker.io docker-compose-v2
sudo usermod -aG docker $USER
# выйти и снова зайти в SSH, чтобы группа docker применилась
```

Проверка Java:

```bash
java -version   # должна быть 17
```

### 5. Server pack

Скачай **serverpack** с CurseForge на ПК, залей на VM (или `wget` прямой ссылки, если есть).

Пример через SCP с твоего Windows (PowerShell, Cloud SDK):

```powershell
gcloud compute scp serverpack.zip skuf-gt:~/ --zone=ТВОЯ_ЗОНА
```

На VM:

```bash
mkdir -p ~/gt-server && cd ~/gt-server
unzip ~/serverpack.zip
# часто внутри start.sh / mods / config — смотри структуру после unzip
chmod +x start.sh 2>/dev/null || true
```

Если пак тянет зависимости скриптом — следуй README пака / `start.sh`.

Первый запуск → согласись с EULA:

```bash
# после первого падения из-за eula:
sed -i 's/eula=false/eula=true/' eula.txt
```

JVM для 16 GB RAM (примерно):

```bash
export JAVA_ARGS="-Xms8G -Xmx12G"
```

(точный старт зависит от `start.sh` пака — правим `-Xmx` там.)

Держать сервер в `screen`:

```bash
screen -S mc
./start.sh   # или java ... как в паке
# Detach: Ctrl+A затем D
# Вернуться: screen -r mc
```

### 6. Наш аддон

Локально:

```powershell
.\gradlew build
```

Jar из `build/libs/` (обычно `skufaddon-0.1.0.jar` или с reobf) → в `mods/` на сервере **рядом с gtceu**.

```powershell
gcloud compute scp build\libs\*.jar skuf-gt:~/gt-server/mods/ --zone=ТВОЯ_ЗОНА
```

Перезапуск MC.

Конфиг наблюдателя на сервере:  
`config/skufaddon-observer.toml` → `baseUrl = "http://127.0.0.1:8080"`.

### 7. Observer (Docker) на той же VM

Из репо скопировать `observer-service/` + `deploy/docker-compose.yml` на VM.

```bash
cd ~/observer
# положить .env с Foundry ключами (НЕ в git)
docker compose up -d --build
curl -s http://127.0.0.1:8080/health
```

### 8. Подключение

В Minecraft Multiplayer: `EXTERNAL_IP:25565`  
У обоих клиентов — **тот же** Community Pack + skufaddon.

`online-mode=true` на публичном сервере (норма). Лицензии Minecraft нужны.

## Экономия кредита

- **Stop** VM когда не играете (диск всё ещё чуть платится, CPU нет)
- Снапшот диска раз в неделю
- Не брать GPU / огромный диск «на всякий»

## Чеклист готовности

- [ ] VM создана, External IP есть  
- [ ] Firewall TCP 25565  
- [ ] Serverpack + eula=true + мир грузится  
- [ ] skufaddon в mods/  
- [ ] observer Docker + `/health` ok  
- [ ] Двое заходят, `<Бог А>` пишет  

---

Дальше в чате: напиши **регион** (belgium / london / frankfurt) и есть ли уже активированный Free Trial — пойдём создавать VM шаг за шагом.
