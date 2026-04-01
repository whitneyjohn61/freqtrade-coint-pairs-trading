#!/usr/bin/env python3
"""stdin: JSON from `freqtrade show-trades --print-json`. stdout: one line per trade, newest open first."""

from __future__ import annotations

import json
import sys


def _trades_from_payload(data: object) -> list[dict]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        if "trades" in data and isinstance(data["trades"], list):
            return [x for x in data["trades"] if isinstance(x, dict)]
    return []


def _sort_key(t: dict) -> float:
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
    raw = sys.stdin.read().strip()
    if not raw:
        print("  (no trades)")
        return
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  (invalid JSON: {e})")
        return
    trades = _trades_from_payload(data)
    if not trades:
        print("  (no trades)")
        return
    trades.sort(key=_sort_key, reverse=True)
    for t in trades:
        tid = t.get("trade_id", t.get("id", "?"))
        pair = t.get("pair", "?")
        is_open = t.get("is_open", False)
        state = "OPEN" if is_open else "CLOSED"
        od = t.get("open_date", "?")
        cd = t.get("close_date")
        cd_part = f" | close={cd}" if cd not in (None, "") else ""
        pr = t.get("profit_ratio")
        pr_part = ""
        if isinstance(pr, (int, float)):
            pr_part = f" | profit_ratio={pr:.6f}"
        print(f"  id={tid} | {pair} | {state} | open={od}{cd_part}{pr_part}")


if __name__ == "__main__":
    main()
