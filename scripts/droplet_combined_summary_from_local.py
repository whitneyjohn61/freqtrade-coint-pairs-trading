#!/usr/bin/env python3
"""Run on your PC: SSH to both Droplets, fetch show-trades JSON per container, print combined markdown table."""

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
    aggregate,
    friendly_label,
    legs_summary,
    markdown_header,
    markdown_row,
    markdown_total_row,
    trades_from_payload,
)


def _ssh_status(user: str, host: str, container: str) -> str:
    cmd = f"docker ps --filter name=^{container}$ --format '{{{{.Status}}}}'"
    r = subprocess.run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=15",
            f"{user}@{host}",
            cmd,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    line = (r.stdout or "").strip().splitlines()
    return line[0] if line else "?"


def _ssh_fetch(user: str, host: str, container: str) -> list[dict]:
    db = CONTAINER_DB_URL[container]
    inner = (
        f"docker exec {container} freqtrade show-trades --db-url {db} --print-json 2>/dev/null"
    )
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", f"{user}@{host}", inner],
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


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--user", default="root")
    p.add_argument("--v01", required=True, help="V01 Droplet host/IP")
    p.add_argument("--v02", required=True, help="V02 Droplet host/IP")
    args = p.parse_args()

    order: list[tuple[str, str, str]] = []
    for c in CONTAINERS_V01:
        order.append((args.v01, c, "V01"))
    for c in CONTAINERS_V02:
        order.append((args.v02, c, "V02"))

    print("")
    print("################################################################################")
    print(" Combined instance summary (all 6 containers)")
    print("################################################################################")
    print("")
    print(markdown_header())

    tot_open = tot_closed = 0
    tot_pnl = 0.0
    tot_stake = 0.0
    mtm_values: list[float | None] = []

    for host, cname, _ in order:
        trades = _ssh_fetch(args.user, host, cname)
        live_map, api_ok = fetch_live_open_pnl_ssh(args.user, host, cname)
        live_use = live_map if api_ok else None
        n_open, n_closed, pnl, _pct, omtm = aggregate(trades, live_use)
        stake = sum(float(t.get("stake_amount") or 0) for t in trades)
        tot_open += n_open
        tot_closed += n_closed
        tot_pnl += pnl
        tot_stake += stake
        mtm_values.append(omtm if api_ok else None)
        pct = (pnl / stake * 100.0) if stake else 0.0
        port = str(CONTAINER_HOST_PORT[cname])
        st = _ssh_status(args.user, host, cname)
        print(
            markdown_row(
                friendly_label(cname),
                port,
                cname,
                st,
                n_open,
                n_closed,
                omtm if api_ok else None,
                pnl,
                pct,
                legs_summary(trades),
            )
        )

    if any(v is None for v in mtm_values):
        tot_mtm: float | None = None
    else:
        tot_mtm = sum(mtm_values)  # type: ignore[arg-type]
    print(markdown_total_row(tot_open, tot_closed, tot_mtm, tot_pnl, tot_stake))
    print("")
    print(
        "Closed trades: `close_profit_abs` from the DB. Open legs: live mark-to-market via "
        "`GET /api/v1/status` (`total_profit_abs`). Total PnL = closed + open MTM."
    )
    print("% column is total PnL / sum(stake_amount) for trades in that instance DB.")
    print("Open MTM shows — if the in-container API call failed (check api_server credentials).")


if __name__ == "__main__":
    main()
