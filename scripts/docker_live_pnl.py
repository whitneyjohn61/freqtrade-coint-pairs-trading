#!/usr/bin/env python3
"""Fetch live mark-to-market PnL per open trade_id via Freqtrade REST /api/v1/status (inside container)."""

from __future__ import annotations

import base64
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

_REPO_SCRIPTS = Path(__file__).resolve().parent
if str(_REPO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_REPO_SCRIPTS))

from instance_summary_lib import CONTAINER_CONFIG_PATH  # noqa: E402

# stdin: ignored; argv[1] = path to config JSON inside container.
# stdout: JSON object mapping trade_id (int as str keys) -> total_profit_abs (float)
_FETCH_STATUS_SCRIPT = r"""import json, sys, base64, math, urllib.request, urllib.error
cfg_path = sys.argv[1]
with open(cfg_path) as f:
    cfg = json.load(f)
api = cfg.get("api_server") or {}
if not api.get("enabled", True):
    print("{}")
    sys.exit(0)
u = api.get("username") or ""
p = api.get("password") or ""
auth = base64.b64encode(f"{u}:{p}".encode()).decode()
req = urllib.request.Request(
    "http://127.0.0.1:8080/api/v1/status",
    headers={"Authorization": "Basic " + auth},
)
try:
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read().decode()
except urllib.error.HTTPError:
    print("{}")
    sys.exit(0)
except Exception:
    print("{}")
    sys.exit(0)
try:
    data = json.loads(raw)
except Exception:
    print("{}")
    sys.exit(0)
if not isinstance(data, list):
    print("{}")
    sys.exit(0)
out = {}
for t in data:
    if not t.get("is_open"):
        continue
    tid = t.get("trade_id")
    if tid is None:
        continue
    v = t.get("total_profit_abs")
    if v is None:
        continue
    try:
        fv = float(v)
    except (TypeError, ValueError):
        continue
    if math.isnan(fv):
        continue
    out[str(int(tid))] = fv
print(json.dumps(out))
"""


def _parse_fetch_stdout(raw: str) -> dict[int, float]:
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[int, float] = {}
    for k, v in data.items():
        try:
            out[int(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def fetch_live_open_pnl_local(container: str) -> tuple[dict[int, float], bool]:
    """Run inside-container status fetch via `docker exec` (caller runs on a host with Docker).

    Returns (trade_id -> total_profit_abs, success). On failure, ({}, False).
    """
    config_path = CONTAINER_CONFIG_PATH.get(container)
    if not config_path:
        return {}, False
    r = subprocess.run(
        ["docker", "exec", "-i", container, "python3", "-", config_path],
        input=_FETCH_STATUS_SCRIPT.encode(),
        capture_output=True,
        check=False,
    )
    if r.returncode != 0:
        return {}, False
    return _parse_fetch_stdout(r.stdout.decode(errors="replace")), True


def fetch_live_open_pnl_ssh(user: str, host: str, container: str) -> tuple[dict[int, float], bool]:
    """SSH to a host, then `docker exec` the same fetch (for combined summary from your PC)."""
    config_path = CONTAINER_CONFIG_PATH.get(container)
    if not config_path:
        return {}, False
    r = subprocess.run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=25",
            f"{user}@{host}",
            "docker",
            "exec",
            "-i",
            container,
            "python3",
            "-",
            config_path,
        ],
        input=_FETCH_STATUS_SCRIPT.encode(),
        capture_output=True,
        check=False,
    )
    if r.returncode != 0:
        return {}, False
    return _parse_fetch_stdout(r.stdout.decode(errors="replace")), True
