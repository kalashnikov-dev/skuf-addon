#!/usr/bin/env bash
# Запускается НА VM (из GitHub Actions по SSH).
# Обновляет jar мода, FTB Quests (аддитивно) и/или Docker observer.
# .env на сервере не трогаем. data.snbt пака не перезаписываем.

set -euo pipefail

MC_DIR="${MC_DIR:-$HOME/GregTech-Modern-Community-Pack/serverpack}"
AI_DIR="${AI_DIR:-$HOME/skuf-ai}"
SCREEN_NAME="${SCREEN_NAME:-mc}"
JAR_SRC="${JAR_SRC:-/tmp/skufaddon-upload.jar}"
QUESTS_SRC="${QUESTS_SRC:-/tmp/skuf-quests-chapters}"

UPDATE_MOD="${UPDATE_MOD:-0}"
UPDATE_OBSERVER="${UPDATE_OBSERVER:-0}"
UPDATE_QUESTS="${UPDATE_QUESTS:-0}"
RESTART_MC="${RESTART_MC:-1}"

echo "== skuf remote-update =="
echo "MC_DIR=$MC_DIR AI_DIR=$AI_DIR UPDATE_MOD=$UPDATE_MOD UPDATE_QUESTS=$UPDATE_QUESTS UPDATE_OBSERVER=$UPDATE_OBSERVER"

restart_minecraft() {
  echo "Restarting Minecraft (screen: $SCREEN_NAME)..."
  if screen -list | grep -q "[.]${SCREEN_NAME}[[:space:]]"; then
    screen -S "$SCREEN_NAME" -p 0 -X stuff $'stop\n' || true
    for i in $(seq 1 60); do
      if ! pgrep -f 'forge.*nogui|run.sh|start.sh' >/dev/null 2>&1; then
        if ! pgrep -af java | grep -qi forge; then
          break
        fi
      fi
      sleep 2
    done
    screen -S "$SCREEN_NAME" -X quit 2>/dev/null || true
    sleep 2
  fi
  pkill -f 'forge-.*\.jar' 2>/dev/null || true
  sleep 2
  cd "$MC_DIR"
  screen -dmS "$SCREEN_NAME" bash -lc "./start.sh"
  echo "Minecraft start requested in screen '$SCREEN_NAME'"
}

NEED_MC_RESTART=0

if [[ "$UPDATE_MOD" == "1" ]]; then
  if [[ ! -f "$JAR_SRC" ]]; then
    echo "ERROR: jar not found at $JAR_SRC"
    exit 1
  fi
  mkdir -p "$MC_DIR/mods"
  rm -f "$MC_DIR/mods"/skufaddon*.jar
  cp -f "$JAR_SRC" "$MC_DIR/mods/skufaddon-0.1.0.jar"
  echo "Installed jar -> $MC_DIR/mods/skufaddon-0.1.0.jar"
  NEED_MC_RESTART=1
fi

if [[ "$UPDATE_QUESTS" == "1" ]]; then
  # Аддитивно: только наши chapter *.snbt рядом с главами Community Pack.
  # НЕ трогаем data.snbt, chapter_groups.snbt, reward_tables и чужие chapters.
  if [[ ! -d "$QUESTS_SRC" ]]; then
    echo "ERROR: quests source dir not found at $QUESTS_SRC"
    exit 1
  fi
  shopt -s nullglob
  files=("$QUESTS_SRC"/*.snbt)
  if [[ ${#files[@]} -eq 0 ]]; then
    echo "ERROR: no .snbt chapter files in $QUESTS_SRC"
    exit 1
  fi
  DEST="$MC_DIR/config/ftbquests/quests/chapters"
  mkdir -p "$DEST"
  cp -f "${files[@]}" "$DEST/"
  echo "Installed ${#files[@]} ArthurTech chapter(s) into $DEST (pack chapters kept)"
  ls -la "$DEST"/steam.snbt "$DEST"/lv.snbt "$DEST"/endgame.snbt 2>/dev/null || true
  NEED_MC_RESTART=1
fi

if [[ "$NEED_MC_RESTART" == "1" && "$RESTART_MC" == "1" ]]; then
  restart_minecraft
fi

if [[ "$UPDATE_OBSERVER" == "1" ]]; then
  if [[ ! -d "$AI_DIR/deploy" ]]; then
    echo "ERROR: $AI_DIR/deploy missing — сначала один раз разверни skuf-ai на VM"
    exit 1
  fi
  cd "$AI_DIR/deploy"
  docker compose up -d --build
  curl -sf http://127.0.0.1:8080/health || echo "WARN: health check failed"
  echo "Observer rebuilt"
fi

echo "== done =="
