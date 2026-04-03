#!/usr/bin/env python3
"""Run on a Droplet: build instance summary table for cointpairs containers on this host (docker exec)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Allow importing instance_summary_lib when run as scripts/droplet_instance_summary_on_host.py
_REPO_SCRIPTS = Path(__file__).resolve().parent
if str(_REPO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_REPO_SCRIPTS))

from docker_live_pnl import fetch_live_open_pnl_local  # noqa: E402
from instance_summary_lib import (  # noqa: E402
    CONTAINER_DB_URL,
    CONTAINER_HOST_PORT,
    aggregate,
    friendly_label,
    legs_summary,
    markdown_header,
    markdown_row,
    markdown_total_row,
    trades_from_payload,
)


def _docker_ps_cointpairs() -> list[str]:
    r = subprocess.run(
        ["docker", "ps", "--filter", "name=cointpairs", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        return []
    names = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    return sorted(names)


def _docker_status(name: str) -> str:
    r = subprocess.run(
        ["docker", "ps", "--filter", f"name=^{name}$", "--format", "{{.Status}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    line = r.stdout.strip().splitlines()
    return line[0] if line else "?"


def _fetch_trades(container: str) -> list[dict]:
    db = CONTAINER_DB_URL.get(container)
    if not db:
        return []
    r = subprocess.run(
        [
            "docker",
            "exec",
            container,
            "freqtrade",
            "show-trades",
            "--db-url",
            db,
            "--print-json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0 or not r.stdout.strip():
        return []
    try:
        data = json.loads(r.stdout)
    except Exception:
        return []
    return trades_from_payload(data)


def main() -> None:
    names = _docker_ps_cointpairs()
    if not names:
        print("")
        print("--- Instance summary (this Droplet) ---")
        print("(no cointpairs containers)")
        return

    rows: list[tuple[int, int, float, float]] = []
    mtm_values: list[float | None] = []
    print("")
    print("--- Instance summary (this Droplet) ---")
    print("")
    print(markdown_header())
    for cname in names:
        trades = _fetch_trades(cname)
        live_map, api_ok = fetch_live_open_pnl_local(cname)
        live_use = live_map if api_ok else None
        n_open, n_closed, pnl, pct, omtm = aggregate(trades, live_use)
        stake = sum(float(t.get("stake_amount") or 0) for t in trades)
        rows.append((n_open, n_closed, pnl, stake))
        mtm_values.append(omtm if api_ok else None)
        port = str(CONTAINER_HOST_PORT.get(cname, "?"))
        st = _docker_status(cname)
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
    to = sum(x[0] for x in rows)
    tc = sum(x[1] for x in rows)
    tp = sum(x[2] for x in rows)
    ts = sum(x[3] for x in rows)
    if any(v is None for v in mtm_values):
        tot_mtm: float | None = None
    else:
        tot_mtm = sum(mtm_values)  # type: ignore[arg-type]
    print(markdown_total_row(to, tc, tot_mtm, tp, ts))
    print("")
    print(
        "Closed trades: `close_profit_abs` from the DB. Open legs: live mark-to-market via "
        "`GET /api/v1/status` (`total_profit_abs`, same as FreqUI). Total PnL = closed + open MTM."
    )
    print("% column is total PnL / sum(stake_amount) for trades in that instance DB.")
    print("Open MTM shows — if the in-container API call failed (check api_server credentials).")


if __name__ == "__main__":
    main()
