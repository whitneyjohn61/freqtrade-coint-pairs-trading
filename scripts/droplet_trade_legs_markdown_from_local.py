#!/usr/bin/env python3
"""SSH to both droplets, emit markdown tables of every trade leg (show-trades + optional live open PnL)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO_SCRIPTS = Path(__file__).resolve().parent
if str(_REPO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_REPO_SCRIPTS))

from docker_live_pnl import fetch_live_open_pnl_ssh  # noqa: E402
from instance_summary_lib import (  # noqa: E402
    CONTAINER_DB_URL,
    CONTAINER_HOST_PORT,
    CONTAINERS_V01,
    CONTAINERS_V02,
    friendly_label,
    leg_pnl,
    trades_from_payload,
)


def _ssh_trades(user: str, host: str, container: str) -> list[dict]:
    db = CONTAINER_DB_URL[container]
    inner = f"docker exec {container} freqtrade show-trades --db-url {db} --print-json 2>/dev/null"
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=25", f"{user}@{host}", inner],
        capture_output=True,
        text=True,
        check=False,
    )
    raw = (r.stdout or "").strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return trades_from_payload(data)


def _side(t: dict) -> str:
    return "short" if t.get("is_short") else "long"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--user", default="root")
    p.add_argument("--v01", default="165.227.165.131")
    p.add_argument("--v02", default="139.59.139.196")
    args = p.parse_args()

    order: list[tuple[str, str]] = [(args.v01, c) for c in CONTAINERS_V01] + [(args.v02, c) for c in CONTAINERS_V02]

    print("")
    print("### Per-leg trade details (all instances)")
    print("")
    print(
        "| Instance | Host port | Trade ID | Pair | Side | Open | Close | Stake (USDT) | "
        "PnL (USDT) | Open? |"
    )
    print(
        "|----------|-----------|----------|------|------|------|-------|--------------|-------------|-------|"
    )

    for host, cname in order:
        trades = _ssh_trades(args.user, host, cname)
        live_map, api_ok = fetch_live_open_pnl_ssh(args.user, host, cname)
        live_use = live_map if api_ok else None
        port = CONTAINER_HOST_PORT[cname]
        label = friendly_label(cname)

        if not trades:
            print(
                f"| {label} | {port} | - | - | - | - | - | - | - | (no trades) |"
            )
            continue

        for t in sorted(trades, key=lambda x: (x.get("trade_id") or 0)):
            tid = t.get("trade_id", "?")
            pair = t.get("pair", "?")
            od = t.get("open_date") or "?"
            cd = t.get("close_date") or ("-" if t.get("is_open") else "?")
            stake = float(t.get("stake_amount") or 0)
            pnl = leg_pnl(t, live_use)
            op = "yes" if t.get("is_open") else "no"
            print(
                f"| {label} | {port} | {tid} | {pair} | {_side(t)} | {od} | {cd} | "
                f"{stake:.2f} | {pnl:.2f} | {op} |"
            )

    print("")
    print(
        "*PnL: closed legs use `close_profit_abs` from the DB; open legs use live `total_profit_abs` "
        "from `/api/v1/status` when the in-container API call succeeds; otherwise DB-only (often 0 for open).*"
    )
    print("")


if __name__ == "__main__":
    main()
