# Deploy (DigitalOcean Droplets)

## Layout

- **Droplet A:** clone this repo, set secrets, `docker compose --profile v01 up -d`  
  Open firewall TCP **22** (SSH) and **8080–8082** (Freqtrade UI), restricted to your IP if possible.

- **Droplet B:** same repo, `docker compose --profile v02 up -d`  
  Open **8083–8085** (or remap ports via compose override if you prefer 8080–8082 on this host only).

## Go-live checklist (each Droplet)

1. **Create** an Ubuntu LTS Droplet with enough **RAM/CPU** for three Freqtrade processes (e.g. **4 GB RAM** minimum; scale up if you see OOM in logs). Add **SSH keys**; avoid password-only SSH.
2. **Firewall (DO Cloud Firewall or UFW):** allow **TCP 22** (SSH) and the profile’s UI ports (**8080–8082** for `v01`, **8083–8085** for `v02`). Prefer **source = your IP** for UI ports, not `0.0.0.0/0`, unless you accept the risk.
3. **Install Docker Engine + Compose v2** on the Droplet (see [Docker docs for Ubuntu](https://docs.docker.com/engine/install/ubuntu/)).
4. **Clone** this repo (HTTPS or SSH): `git clone <repo-url> && cd freqtrade-coint-pairs-trading`
5. **API / UI secrets** (nothing committed): install Python 3, then from repo root:
   ```bash
   python3 scripts/generate_api_secrets.py --password-file config/.api_ui_password.txt
   ```
   Save `config/.api_ui_password.txt` somewhere safe (password manager). **Restart** containers after rotating secrets.
6. **Binance:** edit the three generated files under `config/config_cointpairs_l_phase1*.json` and set **`exchange.key`** and **`exchange.secret`**. Use futures-enabled API keys if you trade USDT-M per config.
7. **Dry run vs live:** templates ship with **`dry_run`: true**. Keep **dry_run true** for smoke testing on DO; set **`dry_run`: false** only when you intentionally want real orders—after keys and risk checks.
8. **Start one profile per Droplet** (do not run both profiles on one small box unless you know you have headroom):
   ```bash
   docker compose --profile v01 pull
   docker compose --profile v01 up -d
   ```
   On the other Droplet, use `--profile v02` instead.
9. **Verify:** open `http://<droplet-ip>:8080` (and `:8081`, `:8082` for v01), log in as **`freqtrader`** with the password from step 5. Confirm three bots and no repeated errors in logs.

## Secrets (summary)

1. **API / UI:** from repo root run `python scripts/generate_api_secrets.py --password-file config/.api_ui_password.txt` so `config/config_cointpairs_l_phase1*.json` exists with strong `jwt_secret_key` + password (files are gitignored).
2. **Exchange:** set `exchange.key` and `exchange.secret` in those same JSON files (or env if you wire it) before live trading.
3. Do not commit keys or generated `config/config_cointpairs_l_phase1*.json`.

## Logs (quick checks)

```bash
docker compose logs -f cointpairs_v01_btceth
grep -iE 'error|warning|disconnect' user_data/logs/freqtrade_v01_btceth.log
```

## Sizing

Three Freqtrade processes per Droplet need enough **RAM/CPU**; upgrade the Droplet if OOM or high CPU persist.
