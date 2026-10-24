#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$ROOT_DIR"
WATCH_FILE=/tmp/proof


printf '%s\n' '[+] Recreating the disposable vulnerable container'
docker compose down --remove-orphans >/dev/null 2>&1 || true
docker compose --progress=quiet build --pull
docker compose up -d --force-recreate

printf '%s\n' '[+] Following vulnerable service logs'
docker compose logs -f --no-color vulnerable &
LOG_PID=$!

cleanup() {
    if kill -0 "$LOG_PID" 2>/dev/null; then
        kill "$LOG_PID" 2>/dev/null || true
        wait "$LOG_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

printf '[+] Initial check: ls -l %s\n' "$WATCH_FILE"
if ! docker compose exec -T vulnerable ls -l -- "$WATCH_FILE"; then
    printf '[.] %s does not exist yet\n' "$WATCH_FILE"
fi

printf '%s\n' '[+] Monitoring the watched file; the ls check repeats until it exists'

while :; do
    if [[ -z "$(docker compose ps --status running -q vulnerable 2>/dev/null)" ]]; then
        printf '%s\n' '[!] Vulnerable container stopped before the watched file appeared' >&2
        exit 1
    fi

    if docker compose exec -T vulnerable ls -l -- "$WATCH_FILE"; then
        printf '%s\n' '[+] Watched file detected; contents:'
        docker compose exec -T vulnerable cat -- "$WATCH_FILE" || true
        printf '%s\n' '[+] Proof detected; stopping monitoring and Docker'
        docker compose down --remove-orphans
        printf '%s\n' '[+] Monitoring stopped; Docker container and network removed'
        break
    fi

    sleep 1
done
