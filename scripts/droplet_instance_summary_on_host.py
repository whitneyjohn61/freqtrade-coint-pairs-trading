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

from instance_summary_lib import (  # noqa: E402
    CONTAINER_DB_URL,
    CONTAINER_HOST_PORT,
    aggregate,
    friendly_label,
    legs_summary,
    markdown_header,
    markdown_row,
    markdown_total_row,
    parse_json_stdin,
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
    print("")
    print("--- Instance summary (this Droplet) ---")
    print("")
    print(markdown_header())
    for cname in names:
        trades = _fetch_trades(cname)
        n_open, n_closed, pnl, pct = aggregate(trades)
        rows.append((n_open, n_closed, pnl, sum(float(t.get("stake_amount") or 0) for t in trades)))
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
                pnl,
                pct,
                legs_summary(trades),
            )
        )
    to = sum(x[0] for x in rows)
    tc = sum(x[1] for x in rows)
    tp = sum(x[2] for x in rows)
    ts = sum(x[3] for x in rows)
    print(markdown_total_row(to, tc, tp, ts))
    print("")
    print("PnL / % use realized `close_profit_abs` (closed) and `profit_abs` when set (open);")
    print("% column is total PnL / sum(stake_amount) for trades in that instance DB.")


if __name__ == "__main__":
    main()
