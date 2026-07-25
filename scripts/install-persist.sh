#!/usr/bin/env bash
# Install user-level systemd unit so the app survives Grok sessions / logouts.
# Run: bash scripts/install-persist.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UNIT_SRC="$ROOT/deploy/tuna-starlink.service"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIT_DST="$UNIT_DIR/tuna-starlink.service"
VENV_UVICORN="$ROOT/backend/.venv/bin/uvicorn"

if [[ ! -x "$VENV_UVICORN" ]]; then
  echo "Missing venv uvicorn at $VENV_UVICORN"
  echo "Run: make install-backend"
  exit 1
fi

if [[ ! -f "$ROOT/backend/.env.local" ]]; then
  echo "WARNING: backend/.env.local not found — API keys may be missing."
fi

mkdir -p "$UNIT_DIR"
# Expand %h is done by systemd; keep unit as shipped (uses %h).
cp "$UNIT_SRC" "$UNIT_DST"

# Stop ad-hoc nohup processes on 8010 so the unit owns the port
if command -v fuser >/dev/null 2>&1; then
  fuser -k 8010/tcp 2>/dev/null || true
  sleep 1
fi

systemctl --user daemon-reload
systemctl --user enable tuna-starlink.service
systemctl --user restart tuna-starlink.service

# Survive logout / Grok session end (user services keep running)
if command -v loginctl >/dev/null 2>&1; then
  loginctl enable-linger "$USER" 2>/dev/null || \
    echo "NOTE: could not enable linger (may need: sudo loginctl enable-linger $USER)"
fi

sleep 2
systemctl --user --no-pager status tuna-starlink.service || true
echo ""
echo "UI:  http://127.0.0.1:8010"
echo "Logs: journalctl --user -u tuna-starlink -f"
echo "      or tail -f $ROOT/uvicorn.log"
echo ""
echo "Stop:    systemctl --user stop tuna-starlink"
echo "Start:   systemctl --user start tuna-starlink"
echo "Disable: systemctl --user disable --now tuna-starlink"
