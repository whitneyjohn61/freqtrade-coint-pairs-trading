#!/usr/bin/env python3
"""Generate api_server jwt_secret_key (per config) and UI password for Freqtrade configs.

Reads JSON from config/templates/, writes config/config_*.json with secrets filled.
Run from repo root: python scripts/generate_api_secrets.py

The generated config/ JSON files are gitignored — do not commit them.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "config" / "templates"
OUT_DIR = ROOT / "config"

CONFIG_NAMES = (
    "config_cointpairs_l_phase1.json",
    "config_cointpairs_l_phase1_bnb_sol.json",
    "config_cointpairs_l_phase1_btc_sol.json",
)


def jwt_secret() -> str:
    return secrets.token_urlsafe(48)


def ui_password() -> str:
    return secrets.token_urlsafe(24)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--password-file",
        type=Path,
        help="Write shared UI password to this file (gitignored path recommended).",
    )
    args = parser.parse_args()

    missing = [n for n in CONFIG_NAMES if not (TEMPLATE_DIR / n).is_file()]
    if missing:
        print("Missing templates:", missing, file=sys.stderr)
        print("Expected under", TEMPLATE_DIR, file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pw = ui_password()

    for name in CONFIG_NAMES:
        path = TEMPLATE_DIR / name
        data = json.loads(path.read_text(encoding="utf-8"))
        data["api_server"]["jwt_secret_key"] = jwt_secret()
        data["api_server"]["password"] = pw
        out = OUT_DIR / name
        out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print("Wrote", out.relative_to(ROOT))

    print()
    print("Username (all instances): freqtrader")
    print("UI password (all instances):", pw)
    print("Store the password in a password manager; rotate with this script if leaked.")

    if args.password_file:
        args.password_file.parent.mkdir(parents=True, exist_ok=True)
        args.password_file.write_text(
            f"freqtrader\n{pw}\n", encoding="utf-8"
        )
        print("Also wrote", args.password_file)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
