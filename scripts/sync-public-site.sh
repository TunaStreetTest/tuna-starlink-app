#!/usr/bin/env bash
# Copy Planet Hack site files to the droplet. Does not touch Caddy, compose, or x-loops.
# Requires deploy/public/.env (not in git): PUBLIC_SSH (root@<ip>).
#
#   sync-public-site.sh ui                 dist/index.html and dist/assets/
#   sync-public-site.sh feed               public/public/feed.json
#   sync-public-site.sh plate <run_id>     feed.json and media/<run_id>.jpg
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/deploy/public/.env"

usage() {
  echo "usage: sync-public-site.sh ui|feed|plate <run_id>" >&2
  exit 2
}

if [[ ! -f "$ENV_FILE" ]]; then
  echo "missing $ENV_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ ! "${PUBLIC_SSH:-}" =~ ^[A-Za-z0-9._@:-]+$ ]]; then
  echo "PUBLIC_SSH must look like root@<ip>" >&2
  exit 1
fi

mode="${1:-}"
case "$mode" in
  ui)
    html="$ROOT/public/dist/index.html"
    assets="$ROOT/public/dist/assets"
    if [[ ! -f "$html" || ! -d "$assets" ]]; then
      echo "missing $html or $assets — build public/ first" >&2
      exit 1
    fi
    ssh "$PUBLIC_SSH" "mkdir -p /root/planethack/site/assets"
    rsync -a "$html" "$PUBLIC_SSH:/root/planethack/site/index.html"
    rsync -a "$assets/" "$PUBLIC_SSH:/root/planethack/site/assets/"
    ;;
  feed)
    feed="$ROOT/public/public/feed.json"
    if [[ ! -f "$feed" ]]; then
      echo "missing $feed" >&2
      exit 1
    fi
    ssh "$PUBLIC_SSH" "mkdir -p /root/planethack/site"
    rsync -a "$feed" "$PUBLIC_SSH:/root/planethack/site/feed.json"
    ;;
  plate)
    run_id="${2:-}"
    if [[ ! "$run_id" =~ ^[A-Za-z0-9_-]+$ ]]; then
      echo "run_id must match [A-Za-z0-9_-]+" >&2
      exit 1
    fi
    feed="$ROOT/public/public/feed.json"
    jpg="$ROOT/public/public/media/${run_id}.jpg"
    if [[ ! -f "$feed" || ! -f "$jpg" ]]; then
      echo "missing feed or $jpg" >&2
      exit 1
    fi
    ssh "$PUBLIC_SSH" "mkdir -p /root/planethack/site/media"
    rsync -a "$feed" "$PUBLIC_SSH:/root/planethack/site/feed.json"
    rsync -a "$jpg" "$PUBLIC_SSH:/root/planethack/site/media/${run_id}.jpg"
    ;;
  *)
    usage
    ;;
esac

echo "synced $mode"
