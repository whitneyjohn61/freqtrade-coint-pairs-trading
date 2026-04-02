# freqtrade-coint-pairs-trading

Standalone forward-test deployment for **Candidate L** (Enhanced Cointegration Pairs): **V01** vs **V02** on **three** Binance USDT-M spreads:

| Config | Pair (traded / anchor) |
|--------|-------------------------|
| `config/config_cointpairs_l_phase1.json` | BTC / ETH |
| `config/config_cointpairs_l_phase1_bnb_sol.json` | BNB / SOL |
| `config/config_cointpairs_l_phase1_btc_sol.json` | BTC / SOL |

Tracked **templates** (placeholders) live under `config/templates/`. **Do not commit** the generated files in `config/` — they contain `jwt_secret_key` and UI `password` (gitignored).

- **Droplet A:** run **V01** only — `docker compose --profile v01 up -d`  
  Web UI: `http://<host>:8080` (BTC/ETH), `:8081` (BNB/SOL), `:8082` (BTC/SOL)

- **Droplet B:** run **V02** only — `docker compose --profile v02 up -d`  
  Web UI: `http://<host>:8083` (BTC/ETH), `:8084` (BNB/SOL), `:8085` (BTC/SOL)

`dry_run` is **true** in templates. Set Binance `exchange.key` / `exchange.secret` before live trading (never commit keys).

## Prerequisites

- Docker + Docker Compose v2  
- Python 3 (once per machine, to generate API secrets into `config/`)  
- This repo (no sibling Freqtrade build): uses `freqtradeorg/freqtrade:stable`

## First-time setup (API secrets)

From the repo root, generate `config/config_cointpairs_l_phase1*.json` with strong `jwt_secret_key` values (one per file) and a shared UI password:

```powershell
cd C:\Work\algo-trading\freqtrade-coint-pairs-trading
python scripts/generate_api_secrets.py --password-file config/.api_ui_password.txt
```

Login: username `freqtrader`, password printed by the script and saved to `config/.api_ui_password.txt` (also gitignored). Re-run the script to rotate secrets; restart containers afterward.

## Quick start (one profile)

```powershell
cd C:\Work\algo-trading\freqtrade-coint-pairs-trading
python scripts/generate_api_secrets.py --password-file config/.api_ui_password.txt
docker compose --profile v01 pull
docker compose --profile v01 up -d
```

Logs: `user_data/logs/freqtrade_v01_*.log` — see also `docker compose logs -f <service>`.

## Strategies

- `EnhancedCointPairsStrategy_V01` / `V02` — pairs come from `config["cointpairs"]` and `pair_whitelist`.  
- **V01** in this repo matches the lab’s dual-leg logic but reads **cointpairs** from config (required for BNB/SOL and BTC/SOL).

## Reference

Lab research / backtests live in a separate repo (`freqtrade-strategy-lab`); this tree is deploy-only.

- **Candidate L docs (copied here):** `user_data/info/EnhancedCointPairs_Deep_Dive.md` (narrative + results summary), `user_data/info/EnhancedCointPairs_Dev_Plan.md` (full dev plan — canonical copy lives in the lab repo).
