#!/usr/bin/env bash
# Snapshot a file before editing it, so a wrong theory can be rolled back.
#   backup.sh <file> "<reason>"
# Copies to backups/<basename>.<UTC timestamp> and appends a line to
# backups/INDEX.md naming the reason. Restoring is a plain cp back.
set -uo pipefail
A=$(cd "$(dirname "$0")" && pwd)
f="$1"; why="${2:-}"
[ -f "$f" ] || { echo "[backup] no such file: $f" >&2; exit 1; }
ts=$(date -u +%Y%m%dT%H%M%SZ)
dst="$A/backups/$(basename "$f").$ts"
cp -p "$f" "$dst"
printf -- '- `%s` -> `backups/%s` @ %s\n  - %s\n' \
  "${f#$A/}" "$(basename "$dst")" "$ts" "$why" >> "$A/backups/INDEX.md"
echo "[backup] $f -> backups/$(basename "$dst")"
