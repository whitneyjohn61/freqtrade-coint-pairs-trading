# freqtrade-coint-pairs-trading

Standalone forward-test deployment for **Candidate L** (Enhanced Cointegration Pairs): **V01** vs **V02** on **three** Binance USDT-M spreads:

| Config | Pair (traded / anchor) |
|--------|-------------------------|
| `config/config_cointpairs_l_phase1.json` | BTC / ETH |
| `config/config_cointpairs_l_phase1_bnb_sol.json` | BNB / SOL |
| `config/config_cointpairs_l_phase1_btc_sol.json` | BTC / SOL |

- **Droplet A:** run **V01** only — `docker compose --profile v01 up -d`  
  Web UI: `http://<host>:8080` (BTC/ETH), `:8081` (BNB/SOL), `:8082` (BTC/SOL)

- **Droplet B:** run **V02** only — `docker compose --profile v02 up -d`  
  Web UI: `http://<host>:8083` (BTC/ETH), `:8084` (BNB/SOL), `:8085` (BTC/SOL)

`dry_run` is **true** in tracked configs. Set Binance keys in config or env before live trading; replace `CHANGE_ME_*` in each config’s `api_server` block (JWT + UI password).

## Prerequisites

- Docker + Docker Compose v2  
- This repo (no sibling Freqtrade build): uses `freqtradeorg/freqtrade:stable`

## Quick start (one profile)

```powershell
cd C:\Work\algo-trading\freqtrade-coint-pairs-trading
docker compose --profile v01 pull
docker compose --profile v01 up -d
```

Logs: `user_data/logs/freqtrade_v01_*.log` — see also `docker compose logs -f <service>`.

## Strategies

- `EnhancedCointPairsStrategy_V01` / `V02` — pairs come from `config["cointpairs"]` and `pair_whitelist`.  
- **V01** in this repo matches the lab’s dual-leg logic but reads **cointpairs** from config (required for BNB/SOL and BTC/SOL).

## Reference

Lab research / backtests live in a separate repo (`freqtrade-strategy-lab`); this tree is deploy-only.
