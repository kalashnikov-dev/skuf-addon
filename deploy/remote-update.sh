#!/usr/bin/env bash
# Запускается НА VM (из GitHub Actions по SSH).
# Обновляет jar мода и/или Docker observer. .env на сервере не трогаем.

set -euo pipefail

MC_DIR="${MC_DIR:-$HOME/GregTech-Modern-Community-Pack/serverpack}"
AI_DIR="${AI_DIR:-$HOME/skuf-ai}"
SCREEN_NAME="${SCREEN_NAME:-mc}"
JAR_SRC="${JAR_SRC:-/tmp/skufaddon-upload.jar}"

UPDATE_MOD="${UPDATE_MOD:-0}"
UPDATE_OBSERVER="${UPDATE_OBSERVER:-0}"
RESTART_MC="${RESTART_MC:-1}"

echo "== skuf remote-update =="
echo "MC_DIR=$MC_DIR AI_DIR=$AI_DIR UPDATE_MOD=$UPDATE_MOD UPDATE_OBSERVER=$UPDATE_OBSERVER"

if [[ "$UPDATE_MOD" == "1" ]]; then
  if [[ ! -f "$JAR_SRC" ]]; then
    echo "ERROR: jar not found at $JAR_SRC"
    exit 1
  fi
  mkdir -p "$MC_DIR/mods"
  # убрать старые версии аддона
  rm -f "$MC_DIR/mods"/skufaddon*.jar
  cp -f "$JAR_SRC" "$MC_DIR/mods/skufaddon-0.1.0.jar"
  echo "Installed jar -> $MC_DIR/mods/skufaddon-0.1.0.jar"

  if [[ "$RESTART_MC" == "1" ]]; then
    echo "Restarting Minecraft (screen: $SCREEN_NAME)..."
    # мягкий stop, если screen жив
    if screen -list | grep -q "[.]${SCREEN_NAME}[[:space:]]"; then
      screen -S "$SCREEN_NAME" -p 0 -X stuff $'stop\n' || true
      # ждём пока java отпустит порт / процесс
      for i in $(seq 1 60); do
        if ! pgrep -f 'forge.*nogui|run.sh|start.sh' >/dev/null 2>&1; then
          # ещё подождём исчезновения java с forge в cmdline
          if ! pgrep -af java | grep -qi forge; then
            break
          fi
        fi
        sleep 2
      done
      # на всякий случай убьём зависший screen
      screen -S "$SCREEN_NAME" -X quit 2>/dev/null || true
      sleep 2
    fi
    # прибить застрявший forge, если stop не сработал
    pkill -f 'forge-.*\.jar' 2>/dev/null || true
    sleep 2

    cd "$MC_DIR"
    screen -dmS "$SCREEN_NAME" bash -lc "./start.sh"
    echo "Minecraft start requested in screen '$SCREEN_NAME'"
  fi
fi

if [[ "$UPDATE_OBSERVER" == "1" ]]; then
  if [[ ! -d "$AI_DIR/deploy" ]]; then
    echo "ERROR: $AI_DIR/deploy missing — сначала один раз разверни skuf-ai на VM"
    exit 1
  fi
  cd "$AI_DIR/deploy"
  # .env уже лежит в ../observer-service/.env на VM
  docker compose up -d --build
  curl -sf http://127.0.0.1:8080/health || echo "WARN: health check failed"
  echo "Observer rebuilt"
fi

echo "== done =="
