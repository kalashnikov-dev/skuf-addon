#!/usr/bin/env bash
# ArthurTech / skufaddon - one-click launcher (GitBash on Windows, also Linux/macOS)
set -u
cd "$(dirname "$0")" || exit 1

echo "=================================================="
echo "  ArthurTech / skufaddon - one-click launcher"
echo "=================================================="
echo

# Print the Java major version of the given java binary (e.g. 17 or 21), or 0.
jmajor() {
  local v
  v=$("${1:-java}" -version 2>&1 | head -1 \
    | sed -E 's/.*version "([0-9]+)(\.([0-9]+))?.*/\1 \3/' \
    | awk '{ if ($1==1) print $2; else print $1 }')
  echo "${v:-0}"
}

# Use current java if it is already >= 17, otherwise try to locate one.
if [ "$(jmajor java 2>/dev/null)" -lt 17 ] 2>/dev/null; then
  # Detect current drive letter on Windows (e.g. /e/)
  _CWD="$(cd "$(dirname "$0")" && pwd)"
  _DRIVE="$(echo "$_CWD" | cut -c1-3)"

  for d in \
      "${JAVA_HOME:-}" \
      "${_DRIVE}/Program Files/Eclipse Adoptium/"jdk-21* \
      "${_DRIVE}/Program Files/Microsoft/"jdk-21* \
      "${_DRIVE}/Program Files/Java/"jdk-21* \
      "${_DRIVE}/Program Files/Eclipse Adoptium/"jdk-17* \
      "${_DRIVE}/Program Files/Java/"jdk-17* \
      "${_DRIVE}/Program Files/Microsoft/"jdk-17* \
      /usr/lib/jvm/*21* \
      /usr/lib/jvm/*17* \
      /Library/Java/JavaVirtualMachines/*21*/Contents/Home \
      /Library/Java/JavaVirtualMachines/*17*/Contents/Home ; do
    [ -n "$d" ] && [ -x "$d/bin/java" ] || continue
    if [ "$(jmajor "$d/bin/java")" -ge 17 ] 2>/dev/null; then
      export JAVA_HOME="$d"
      export PATH="$d/bin:$PATH"
      break
    fi
  done
fi

if [ "$(jmajor java 2>/dev/null)" -lt 17 ] 2>/dev/null; then
  echo "[!] Java 17+ not found."
  echo "    Install Temurin 17+: https://adoptium.net/temurin/releases/?version=17"
  echo "    Or: export JAVA_HOME=/path/to/jdk-17  (then run again)"
  read -r -p "Press Enter to exit..." _
  exit 1
fi

echo "Java OK:"
java -version
chmod +x ./gradlew 2>/dev/null

echo
echo "Choose action:"
echo "  [1] Play    (runClient)  - launch the game with the mod   (default)"
echo "  [2] Build   (build)      - make build/libs/skufaddon-0.1.0.jar"
echo "  [3] Server  (runServer)  - dedicated server, no graphics"
echo "  [4] Datagen (runData)    - regenerate item models / lang"
echo
read -r -p "Enter 1-4 [default 1]: " CHOICE
case "${CHOICE:-1}" in
  2) TASK=build ;;
  3) TASK=runServer ;;
  4) TASK=runData ;;
  *) TASK=runClient ;;
esac

echo
echo ">> ./gradlew $TASK   (first run downloads Forge/MC/GTCEu, be patient)"
echo
./gradlew "$TASK" --no-daemon --console=plain
RC=$?
echo
echo "Done. exit code $RC"
read -r -p "Press Enter to close..." _
exit $RC
