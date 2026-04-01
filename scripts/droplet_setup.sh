#!/usr/bin/env bash
# Run on the Ubuntu Droplet as root (local or via SSH pipe).
# Installs Docker, clones this repo, generates API config JSON, starts compose.
#
# Environment (optional):
#   FT_COMPOSE_PROFILE   v01 or v02 (default: v01)
#   FT_REPO_URL          git clone URL (default: GitHub HTTPS for this repo)
#   FT_INSTALL_DIR       install path (default: $HOME/freqtrade-coint-pairs-trading)
#   FT_SKIP_COMPOSE      if 1, do not run docker compose up
#   FT_SKIP_SECRETS      if 1, skip generate_api_secrets when configs already exist (default: generate if any missing)
#   FT_GIT_SSH_COMMAND   optional; passed to GIT_SSH_COMMAND for git@ clone (Deploy key)

set -euo pipefail

FT_COMPOSE_PROFILE="${FT_COMPOSE_PROFILE:-v01}"
FT_REPO_URL="${FT_REPO_URL:-https://github.com/whitneyjohn61/freqtrade-coint-pairs-trading.git}"
FT_INSTALL_DIR="${FT_INSTALL_DIR:-$HOME/freqtrade-coint-pairs-trading}"
FT_SKIP_COMPOSE="${FT_SKIP_COMPOSE:-0}"
FT_SKIP_SECRETS="${FT_SKIP_SECRETS:-0}"

if [[ "${FT_COMPOSE_PROFILE}" != "v01" && "${FT_COMPOSE_PROFILE}" != "v02" ]]; then
  echo "FT_COMPOSE_PROFILE must be v01 or v02, got: ${FT_COMPOSE_PROFILE}" >&2
  exit 1
fi

if [[ "${EUID:-0}" -ne 0 ]]; then
  echo "Run as root on the Droplet, e.g.: sudo bash droplet_setup.sh" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

install_docker() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "[droplet_setup] Docker already installed."
    return 0
  fi

  echo "[droplet_setup] Installing Docker Engine + Compose plugin..."
  apt-get update -qq
  apt-get install -y ca-certificates curl

  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc

  # shellcheck source=/dev/null
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    | tee /etc/apt/sources.list.d/docker.list >/dev/null

  apt-get update -qq
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  systemctl enable --now docker
  docker run --rm hello-world >/dev/null
  echo "[droplet_setup] Docker OK: $(docker --version)"
}

install_docker

apt-get install -y git python3

# Avoid interactive "Username for https://github.com" on headless servers (private HTTPS clone fails).
export GIT_TERMINAL_PROMPT=0
# Optional: for git@github.com clone with a Deploy key, e.g.
#   export FT_GIT_SSH_COMMAND='ssh -i ~/.ssh/github_deploy -o IdentitiesOnly=yes'
if [[ -n "${FT_GIT_SSH_COMMAND:-}" ]]; then
  export GIT_SSH_COMMAND="${FT_GIT_SSH_COMMAND}"
fi

if [[ ! -d "${FT_INSTALL_DIR}/.git" ]]; then
  echo "[droplet_setup] Cloning ${FT_REPO_URL} -> ${FT_INSTALL_DIR}"
  if ! git clone "${FT_REPO_URL}" "${FT_INSTALL_DIR}"; then
    echo "" >&2
    echo "[droplet_setup] ERROR: git clone failed." >&2
    echo "  If the repo is PRIVATE, HTTPS cannot ask for a password on the Droplet." >&2
    echo "  Fix one of:" >&2
    echo "    A) GitHub → repo Settings → General → Danger zone → Change visibility → Public" >&2
    echo "    B) Use SSH: add a Deploy key (repo → Settings → Deploy keys), then on the Droplet:" >&2
    echo "       ssh-keygen -t ed25519 -N '' -f ~/.ssh/github_deploy" >&2
    echo "       cat ~/.ssh/github_deploy.pub   # paste into GitHub Deploy keys" >&2
    echo "       export FT_REPO_URL=git@github.com:whitneyjohn61/freqtrade-coint-pairs-trading.git" >&2
    echo "       export GIT_SSH_COMMAND='ssh -i ~/.ssh/github_deploy -o IdentitiesOnly=yes'" >&2
    echo "       bash scripts/droplet_setup.sh" >&2
    exit 1
  fi
else
  echo "[droplet_setup] Repo exists; pulling latest"
  git -C "${FT_INSTALL_DIR}" pull --ff-only || {
    echo "[droplet_setup] git pull failed (private repo / auth?). See clone error hints above." >&2
    exit 1
  }
fi

cd "${FT_INSTALL_DIR}"

need_secrets=0
for f in config_cointpairs_l_phase1.json config_cointpairs_l_phase1_bnb_sol.json config_cointpairs_l_phase1_btc_sol.json; do
  if [[ ! -f "config/${f}" ]]; then
    need_secrets=1
    break
  fi
done

if [[ "${need_secrets}" -eq 1 && "${FT_SKIP_SECRETS}" != "1" ]]; then
  echo "[droplet_setup] Generating API JWT + UI password into config/*.json"
  python3 scripts/generate_api_secrets.py --password-file config/.api_ui_password.txt
  chmod 600 config/.api_ui_password.txt 2>/dev/null || true
elif [[ "${need_secrets}" -eq 1 ]]; then
  echo "[droplet_setup] Missing config JSON but FT_SKIP_SECRETS=1; fix manually." >&2
  exit 1
else
  echo "[droplet_setup] config/config_cointpairs_l_phase1*.json already present; skipping generate_api_secrets"
fi

echo ""
echo "[droplet_setup] Next manual steps:"
echo "  - Add Binance exchange.key / exchange.secret in the three config files under config/"
echo "  - Keep dry_run true until ready; then set dry_run false for live trading"
echo "  - UI login: user freqtrader, password in config/.api_ui_password.txt"
echo ""

if [[ "${FT_SKIP_COMPOSE}" == "1" ]]; then
  echo "[droplet_setup] FT_SKIP_COMPOSE=1 — not starting containers."
  echo "  When ready: cd ${FT_INSTALL_DIR} && docker compose --profile ${FT_COMPOSE_PROFILE} up -d"
  exit 0
fi

# Official image runs as UID 1000 (ftuser). Host-owned user_data/logs causes logging to fail and crash loop.
if [[ -d user_data ]]; then
  echo "[droplet_setup] chown -R 1000:1000 user_data (ftuser in container)"
  chown -R 1000:1000 user_data || true
fi

echo "[droplet_setup] docker compose --profile ${FT_COMPOSE_PROFILE} pull && up -d"
docker compose --profile "${FT_COMPOSE_PROFILE}" pull
docker compose --profile "${FT_COMPOSE_PROFILE}" up -d

echo "[droplet_setup] Done. Check: docker compose ps"
case "${FT_COMPOSE_PROFILE}" in
  v01) echo "  FreqUI: http://<this-droplet-ip>:8080  :8081  :8082" ;;
  v02) echo "  FreqUI: http://<this-droplet-ip>:8083  :8084  :8085" ;;
esac
