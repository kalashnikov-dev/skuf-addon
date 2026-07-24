#!/usr/bin/env bash
# Добавляет рестриктнутый pubkey друга в ~/.ssh/authorized_keys на VM.
# Usage: ./setup-friend-ssh.sh /path/to/friend.pub
set -euo pipefail

PUBFILE="${1:-}"
if [[ -z "$PUBFILE" || ! -f "$PUBFILE" ]]; then
  echo "Usage: $0 /path/to/skuf_mcp_friend.pub" >&2
  exit 1
fi

PUBKEY="$(tr -d '\r\n' < "$PUBFILE")"
# Только туннель на observer (+ опционально RCON). Без shell.
LINE="restrict,port-forwarding,permitopen=\"127.0.0.1:8080\",permitopen=\"127.0.0.1:25575\",command=\"/bin/false\" ${PUBKEY}"

AUTH="${HOME}/.ssh/authorized_keys"
mkdir -p "${HOME}/.ssh"
chmod 700 "${HOME}/.ssh"
touch "$AUTH"
chmod 600 "$AUTH"

if grep -Fq "$PUBKEY" "$AUTH" 2>/dev/null; then
  echo "This pubkey is already present in $AUTH — edit the options line manually if needed."
  exit 0
fi

echo "$LINE" >> "$AUTH"
echo "Appended restricted key to $AUTH"
echo "Friend tunnel test:"
echo "  ssh -i skuf_mcp_friend -N -L 8080:localhost:8080 ${USER}@<GCP_HOST>"
