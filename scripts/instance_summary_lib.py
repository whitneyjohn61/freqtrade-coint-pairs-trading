#!/usr/bin/env python3
"""Shared helpers for instance summary tables (open/closed counts, PnL, leg summary)."""

from __future__ import annotations

import json
import re
from typing import Any

_SPREAD_LABEL = {
    "btceth": "BTC/ETH",
    "bnbsol": "BNB/SOL",
    "btcsol": "BTC/SOL",
}


def trades_from_payload(data: object) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        if "trades" in data and isinstance(data["trades"], list):
            return [x for x in data["trades"] if isinstance(x, dict)]
    return []


def friendly_label(container_name: str) -> str:
    m = re.match(r"cointpairs_v(\d+)_(.+)", container_name)
    if not m:
        return container_name
    ver, key = m.groups()
    spread = _SPREAD_LABEL.get(key.lower())
    if spread:
        return f"V{ver} {spread}"
    return container_name


def leg_pnl(t: dict[str, Any]) -> float:
    if not t.get("is_open"):
        v = t.get("close_profit_abs")
        if v is not None:
            return float(v)
        v = t.get("realized_profit")
        if v is not None:
            return float(v)
        return 0.0
    v = t.get("profit_abs")
    if v is not None:
        return float(v)
    return 0.0


def aggregate(trades: list[dict[str, Any]]) -> tuple[int, int, float, float]:
    n_open = sum(1 for t in trades if t.get("is_open"))
    n_closed = sum(1 for t in trades if not t.get("is_open"))
    total_pnl = sum(leg_pnl(t) for t in trades)
    stake = sum(float(t.get("stake_amount") or 0) for t in trades)
    pct = (total_pnl / stake * 100.0) if stake else 0.0
    return n_open, n_closed, total_pnl, pct


def legs_summary(trades: list[dict[str, Any]]) -> str:
    opens = [t for t in trades if t.get("is_open")]
    if not opens:
        return "No open legs"
    parts: list[str] = []
    for t in opens:
        pair = t.get("pair") or ""
        base = pair.split("/")[0] if pair else "?"
        side = "short" if t.get("is_short") else "long"
        parts.append(f"{base} {side}")
    return ", ".join(parts)


def esc_cell(s: str) -> str:
    return s.replace("|", "\\|")


def markdown_row(
    instance_label: str,
    host_port: str,
    container_name: str,
    docker_status: str,
    n_open: int,
    n_closed: int,
    total_pnl: float,
    pct: float,
    legs: str,
) -> str:
    docker_cell = esc_cell(f"{container_name}<br>{docker_status}")
    legs_cell = esc_cell(legs.replace(", ", ",<br>"))
    return (
        f"| **{esc_cell(instance_label)}** | {esc_cell(host_port)} | {docker_cell} | {n_open} | {n_closed} | "
        f"{total_pnl:.2f} | {pct:.2f}% | {legs_cell} |"
    )


def markdown_header() -> str:
    return (
        "| Instance | Host port | Docker | Open | Closed | Total PnL (USDT) | Total %PnL | Open legs (summary) |\n"
        "|----------|-----------|--------|------|--------|------------------|------------|----------------------|"
    )


def markdown_total_row(
    n_open: int,
    n_closed: int,
    total_pnl: float,
    stake_sum: float,
) -> str:
    pct = (total_pnl / stake_sum * 100.0) if stake_sum else 0.0
    dash = "-"
    return (
        f"| **All instances** | {dash} | {dash} | "
        f"**{n_open}** | **{n_closed}** | **{total_pnl:.2f}** | **{pct:.2f}%** | {dash} |"
    )


def parse_json_stdin(raw: str) -> list[dict[str, Any]]:
    raw = raw.strip()
    if not raw:
        return []
    data = json.loads(raw)
    return trades_from_payload(data)


# Same DB URLs as scripts/droplet_status_remote.sh
CONTAINER_DB_URL: dict[str, str] = {
    "cointpairs_v01_btceth": "sqlite:////freqtrade/user_data/tradesv3.v01.btceth.sqlite",
    "cointpairs_v01_bnbsol": "sqlite:////freqtrade/user_data/tradesv3.v01.bnbsol.sqlite",
    "cointpairs_v01_btcsol": "sqlite:////freqtrade/user_data/tradesv3.v01.btcsol.sqlite",
    "cointpairs_v02_btceth": "sqlite:////freqtrade/user_data/tradesv3.v02.btceth.sqlite",
    "cointpairs_v02_bnbsol": "sqlite:////freqtrade/user_data/tradesv3.v02.bnbsol.sqlite",
    "cointpairs_v02_btcsol": "sqlite:////freqtrade/user_data/tradesv3.v02.btcsol.sqlite",
}

# Host port mapping (host 8080 -> container 8080)
CONTAINER_HOST_PORT: dict[str, int] = {
    "cointpairs_v01_btceth": 8080,
    "cointpairs_v01_bnbsol": 8081,
    "cointpairs_v01_btcsol": 8082,
    "cointpairs_v02_btceth": 8083,
    "cointpairs_v02_bnbsol": 8084,
    "cointpairs_v02_btcsol": 8085,
}

CONTAINERS_V01 = (
    "cointpairs_v01_btceth",
    "cointpairs_v01_bnbsol",
    "cointpairs_v01_btcsol",
)
CONTAINERS_V02 = (
    "cointpairs_v02_btceth",
    "cointpairs_v02_bnbsol",
    "cointpairs_v02_btcsol",
)
