#!/usr/bin/env bash
# Build the public television and rsync it to the droplet.
# Requires deploy/public/.env (not in git): PUBLIC_HOST, PUBLIC_SSH.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/deploy/public/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "missing $ENV_FILE — copy deploy/public/.env.example and fill it in" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ ! "${PUBLIC_HOST:-}" =~ ^[A-Za-z0-9.-]+$ ]]; then
  echo "PUBLIC_HOST must be a hostname" >&2
  exit 1
fi
if [[ ! "${PUBLIC_SSH:-}" =~ ^[A-Za-z0-9._@:-]+$ ]]; then
  echo "PUBLIC_SSH must look like root@<ip>" >&2
  exit 1
fi

PY="$ROOT/backend/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY=python3
fi

"$PY" "$ROOT/scripts/export_public_feed.py"
if ! command -v pnpm >/dev/null; then
  corepack enable
  corepack prepare pnpm@9.15.9 --activate
fi
(cd "$ROOT/public" && pnpm build)

ssh "$PUBLIC_SSH" "mkdir -p /root/planethack/site && printf 'PUBLIC_HOST=%s\n' '$PUBLIC_HOST' > /root/planethack/.env"
ssh "$PUBLIC_SSH" 'if ! command -v docker >/dev/null; then apt-get update && apt-get install -y docker.io docker-compose-v2 && systemctl enable --now docker; fi'
ssh "$PUBLIC_SSH" 'if ! ufw status | grep -q "Status: active"; then ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable; fi'

rsync -a "$ROOT/deploy/public/Caddyfile" "$ROOT/deploy/public/docker-compose.yml" "$PUBLIC_SSH:/root/planethack/"
rsync -a --delete "$ROOT/public/dist/" "$PUBLIC_SSH:/root/planethack/site/"
ssh "$PUBLIC_SSH" "cd /root/planethack && docker compose up -d"
echo "pushed to $PUBLIC_SSH"
