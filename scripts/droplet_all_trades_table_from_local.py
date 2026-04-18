#!/usr/bin/env python3
"""From your PC: SSH to both Droplets, fetch all trades per container, print one combined markdown table.

Sorted by open time (newest first). Open legs use live MTM PnL when the in-container API succeeds."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

_REPO_SCRIPTS = Path(__file__).resolve().parent
if str(_REPO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_REPO_SCRIPTS))

from docker_live_pnl import fetch_live_open_pnl_ssh  # noqa: E402
from instance_summary_lib import (  # noqa: E402
    CONTAINER_DB_URL,
    CONTAINER_HOST_PORT,
    CONTAINERS_V01,
    CONTAINERS_V02,
    esc_cell,
    friendly_label,
    leg_pnl,
    trades_from_payload,
)


def _ssh_fetch(user: str, host: str, container: str) -> list[dict[str, Any]]:
    db = CONTAINER_DB_URL[container]
    inner = (
        f"docker exec {container} freqtrade show-trades --db-url {db} --print-json 2>/dev/null"
    )
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


def _open_sort_ts(t: dict[str, Any]) -> float:
    ts = t.get("open_timestamp")
    if ts is not None:
        try:
            return float(ts)
        except (TypeError, ValueError):
            pass
    od = t.get("open_date")
    if isinstance(od, (int, float)):
        try:
            return float(od)
        except (TypeError, ValueError):
            pass
    return 0.0


def main() -> None:
    p = argparse.ArgumentParser(description="Combined table of all open and closed trades (6 containers).")
    p.add_argument("--user", default="root")
    p.add_argument("--v01", default="165.227.165.131", help="V01 Droplet host/IP")
    p.add_argument("--v02", default="139.59.139.196", help="V02 Droplet host/IP")
    args = p.parse_args()

    order: list[tuple[str, str]] = []
    for c in CONTAINERS_V01:
        order.append((args.v01, c))
    for c in CONTAINERS_V02:
        order.append((args.v02, c))

    flat: list[tuple[dict[str, Any], str, str, dict[int, float] | None]] = []
    for host, cname in order:
        trades = _ssh_fetch(args.user, host, cname)
        live_map, api_ok = fetch_live_open_pnl_ssh(args.user, host, cname)
        live_use: dict[int, float] | None = live_map if api_ok else None
        label = friendly_label(cname)
        port = str(CONTAINER_HOST_PORT[cname])
        for t in trades:
            flat.append((t, label, port, live_use))

    flat.sort(key=lambda x: _open_sort_ts(x[0]), reverse=True)

    print("")
    print("################################################################################")
    print(" All trades (open + closed), newest open time first")
    print("################################################################################")
    print("")
    print(
        "| Open date | Instance | Port | Trade ID | Pair | Side | Status | Close date | "
        "Stake (USDT) | PnL (USDT) |"
    )
    print(
        "|-----------|----------|------|----------|------|------|--------|------------|"
        "--------------|------------|"
    )

    for t, label, port, live_use in flat:
        tid = t.get("trade_id", t.get("id", "?"))
        pair = str(t.get("pair") or "")
        side = "short" if t.get("is_short") else "long"
        is_open = bool(t.get("is_open"))
        status = "OPEN" if is_open else "CLOSED"
        od = str(t.get("open_date") or "")
        cd = str(t.get("close_date") or "")
        if not cd or cd == "None":
            cd = "-"
        stake = float(t.get("stake_amount") or 0)
        pnl = leg_pnl(t, live_use)
        print(
            f"| {esc_cell(od)} | {esc_cell(label)} | {port} | {tid} | {esc_cell(pair)} | {side} | {status} | "
            f"{esc_cell(cd)} | {stake:.2f} | {pnl:.2f} |"
        )

    print("")
    print(f"Rows: **{len(flat)}** (open PnL from live API when available; closed from DB).")
    print("")


if __name__ == "__main__":
    main()
