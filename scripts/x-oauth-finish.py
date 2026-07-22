#!/usr/bin/env python3
"""Finish OAuth1 pin flow and write @tunastarlink tokens into backend/.env.local.

Usage (from repo root or backend):
  python scripts/x-oauth-finish.py 1234567

Prereq: scripts/x-oauth-start (or agent) wrote /tmp/tsl-oauth-request.txt
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import tweepy

REQ = Path("/tmp/tsl-oauth-request.txt")
ENV_LOCAL = Path(__file__).resolve().parents[1] / "backend" / ".env.local"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/x-oauth-finish.py <PIN>")
        return 2
    pin = sys.argv[1].strip()
    if not REQ.is_file():
        print("Missing /tmp/tsl-oauth-request.txt — start OAuth first.")
        return 1

    token, token_secret, api_key, api_secret = REQ.read_text().splitlines()[:4]
    oauth = tweepy.OAuth1UserHandler(api_key, api_secret, callback="oob")
    oauth.request_token = {
        "oauth_token": token,
        "oauth_token_secret": token_secret,
    }
    access_token, access_secret = oauth.get_access_token(pin)

    # Optional: verify who we got
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )
    me = client.get_me(user_auth=True)
    username = None
    if me and me.data:
        username = getattr(me.data, "username", None) or me.data.get("username")
    print(f"Authorized as: @{username}" if username else "Authorized (username unknown)")

    # Write into .env.local — replace access token pair only; keep app keys
    text = ENV_LOCAL.read_text() if ENV_LOCAL.exists() else ""
    lines = []
    skip_keys = {
        "X_ACCESS_TOKEN",
        "X_ACCESS_TOKEN_SECRET",
        "X_ACCOUNT_HANDLE",
    }
    for line in text.splitlines():
        s = line.strip()
        if any(s.startswith(f"{k}=") or s.startswith(f"#{k}=") for k in skip_keys):
            continue
        if s.startswith("# X OAuth") or "posting identity" in s.lower():
            continue
        lines.append(line)
    while lines and lines[-1].strip() == "":
        lines.pop()
    lines.append("")
    lines.append("# X user tokens — @tunastarlink (OAuth pin flow)")
    lines.append(f"X_ACCESS_TOKEN={access_token}")
    lines.append(f"X_ACCESS_TOKEN_SECRET={access_secret}")
    lines.append("X_ACCOUNT_HANDLE=@tunastarlink")
    # ensure app keys exist
    if not any(l.startswith("X_API_KEY=") for l in lines):
        lines.append(f"X_API_KEY={api_key}")
    if not any(l.startswith("X_API_SECRET=") for l in lines):
        lines.append(f"X_API_SECRET={api_secret}")

    ENV_LOCAL.write_text("\n".join(lines) + "\n")
    print(f"Wrote tokens to {ENV_LOCAL}")
    print("Restart backend: cd ~/tuna-starlink-app && make backend")
    try:
        REQ.unlink()
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
