# Deploy (DigitalOcean Droplets)

## Layout

- **Droplet A:** clone this repo, set secrets, `docker compose --profile v01 up -d`  
  Open firewall TCP **22** (SSH) and **8080–8082** (Freqtrade UI), restricted to your IP if possible.

- **Droplet B:** same repo, `docker compose --profile v02 up -d`  
  Open **8083–8085** (or remap ports via compose override if you prefer 8080–8082 on this host only).

## Automated setup (optional)

From your **Windows PC**, in a clone of this repo, you can pipe the remote setup script over SSH (installs Docker, clones/pulls repo, generates API secrets, starts compose):

```powershell
cd C:\Work\algo-trading\freqtrade-coint-pairs-trading
.\scripts\droplet_setup_from_local.ps1 -DropletHost YOUR_DROPLET_IP -ComposeProfile v01
```

Use **`v01`** on the first Droplet and **`v02`** on the second. Example for a second Droplet at `139.59.139.196`:

```powershell
.\scripts\droplet_setup_from_local.ps1 -DropletHost 139.59.139.196 -ComposeProfile v02
```

**On the Droplet only** (from the repo root, after clone or `git pull`), run as **root**:

```bash
cd ~/freqtrade-coint-pairs-trading
bash scripts/droplet_setup.sh
# other profile:
FT_COMPOSE_PROFILE=v02 bash scripts/droplet_setup.sh
```

Environment variables: `FT_COMPOSE_PROFILE`, `FT_REPO_URL`, `FT_INSTALL_DIR`, `FT_SKIP_COMPOSE=1` (install only, do not start containers), `FT_SKIP_SECRETS=1` (skip generating config if you manage files yourself). See `scripts/droplet_setup.sh` for details.

After any automated run, still **add Binance keys** and confirm **`dry_run`** before live trading.

### `ERR_EMPTY_RESPONSE` / UI won’t load (containers restarting)

The Freqtrade image runs as **UID 1000** (`ftuser`). If **`user_data`** on the host is owned by **root**, log files cannot be created and the bot **exits** (`Unable to configure handler 'file'`). Fix on the Droplet:

```bash
chown -R 1000:1000 /root/freqtrade-coint-pairs-trading/user_data
cd /root/freqtrade-coint-pairs-trading && docker compose --profile v01 up -d --force-recreate
```

(Use `--profile v02` on the V02 Droplet.) Newer **`scripts/droplet_setup.sh`** runs this `chown` automatically before `docker compose up`.

### Status summary (all 6 instances without opening each UI)

From your **Windows** PC (same SSH keys as deploy), in a clone of the repo:

```powershell
cd C:\Work\algo-trading\freqtrade-coint-pairs-trading
git pull
.\scripts\droplet_status_from_local.ps1
```

Defaults: **V01** = `165.227.165.131`, **V02** = `139.59.139.196`. Override: `-V01Host`, `-V02Host`. Faster (no `freqtrade show-trades`): `-SkipTrades`. More log lines: `-LogTail 40`.

This SSHs to **both** Droplets and prints **docker** state, **log tails** per `freqtrade_*.log`, and (unless `-SkipTrades`) a **truncated `show-trades`** per container.

### Private GitHub repo / `could not read Username for 'https://github.com'`

HTTPS clone on a Droplet **cannot** open a login prompt. If the repo is **private**, either:

- **Make the repo public** (GitHub → **Settings** → **General** → **Danger zone** → **Change repository visibility**), then re-run the setup script, **or**
- **Use SSH with a Deploy key:** Repo → **Settings** → **Deploy keys** → **Add deploy key** (read-only). On the Droplet, create `ssh-keygen -t ed25519 -N '' -f ~/.ssh/github_deploy`, paste the `.pub` into GitHub, then:

  ```bash
  export FT_REPO_URL=git@github.com:whitneyjohn61/freqtrade-coint-pairs-trading.git
  export GIT_SSH_COMMAND='ssh -i ~/.ssh/github_deploy -o IdentitiesOnly=yes'
  bash scripts/droplet_setup.sh
  ```

From PowerShell, after the Deploy key exists on the Droplet at `~/.ssh/github_deploy`:

```powershell
.\scripts\droplet_setup_from_local.ps1 -DropletHost YOUR_IP -ComposeProfile v02 `
  -RepoUrl "git@github.com:whitneyjohn61/freqtrade-coint-pairs-trading.git" `
  -GitSshCommand "ssh -i ~/.ssh/github_deploy -o IdentitiesOnly=yes"
```

## Go-live checklist (each Droplet)

1. **Create** an Ubuntu LTS Droplet with enough **RAM/CPU** for three Freqtrade processes (e.g. **4 GB RAM** minimum; scale up if you see OOM in logs). Add **SSH keys**; avoid password-only SSH.
2. **Firewall (DO Cloud Firewall or UFW):** allow **TCP 22** (SSH) and the profile’s UI ports (**8080–8082** for `v01`, **8083–8085** for `v02`). Prefer **source = your IP** for UI ports, not `0.0.0.0/0`, unless you accept the risk.
3. **Install Docker Engine + Compose v2** on the Droplet — use [Docker docs for Ubuntu](https://docs.docker.com/engine/install/ubuntu/), or run **`scripts/droplet_setup_from_local.ps1`** / **`scripts/droplet_setup.sh`** (see **Automated setup** above).
4. **Clone** this repo (HTTPS or SSH): `git clone <repo-url> && cd freqtrade-coint-pairs-trading` — skipped if you used the automated script.
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
