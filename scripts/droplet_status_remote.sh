#!/usr/bin/env bash
# Run on a Droplet (as root) to summarize all cointpairs_* containers: docker state, logs, optional trades.
# Env: FT_REPO_ROOT (default /root/freqtrade-coint-pairs-trading), FT_LOG_TAIL (default 18), FT_SKIP_TRADES=1 to skip show-trades

set -uo pipefail

REPO="${FT_REPO_ROOT:-/root/freqtrade-coint-pairs-trading}"
LOG_TAIL="${FT_LOG_TAIL:-18}"
SKIP_TRADES="${FT_SKIP_TRADES:-0}"

db_url_for() {
  case "$1" in
    cointpairs_v01_btceth) echo "sqlite:////freqtrade/user_data/tradesv3.v01.btceth.sqlite" ;;
    cointpairs_v01_bnbsol) echo "sqlite:////freqtrade/user_data/tradesv3.v01.bnbsol.sqlite" ;;
    cointpairs_v01_btcsol) echo "sqlite:////freqtrade/user_data/tradesv3.v01.btcsol.sqlite" ;;
    cointpairs_v02_btceth) echo "sqlite:////freqtrade/user_data/tradesv3.v02.btceth.sqlite" ;;
    cointpairs_v02_bnbsol) echo "sqlite:////freqtrade/user_data/tradesv3.v02.bnbsol.sqlite" ;;
    cointpairs_v02_btcsol) echo "sqlite:////freqtrade/user_data/tradesv3.v02.btcsol.sqlite" ;;
    *) echo "" ;;
  esac
}

echo "================================================================================"
echo "Host: $(hostname)  |  UTC: $(date -u +"%Y-%m-%d %H:%M:%S")"
echo "Repo: ${REPO}"
echo "================================================================================"

echo ""
echo "--- Docker (cointpairs) ---"
if ! docker ps -a --filter "name=cointpairs" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | grep -q cointpairs; then
  echo "(no cointpairs containers found)"
else
  docker ps -a --filter "name=cointpairs" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
fi

echo ""
echo "--- Log tail (last ${LOG_TAIL} lines per file) ---"
shopt -s nullglob
logs=( "${REPO}/user_data/logs"/freqtrade_*.log )
if [[ ${#logs[@]} -eq 0 ]]; then
  echo "(no freqtrade_*.log under ${REPO}/user_data/logs)"
else
  for f in "${logs[@]}"; do
    echo ""
    echo ">>> $(basename "$f") <<<"
    tail -n "${LOG_TAIL}" "$f" 2>/dev/null || echo "(unreadable)"
  done
fi

if [[ "${SKIP_TRADES}" == "1" ]]; then
  echo ""
  echo "--- show-trades skipped (FT_SKIP_TRADES=1) ---"
  exit 0
fi

echo ""
echo "--- Open / recent trades (freqtrade show-trades, truncated) ---"
while IFS= read -r cname; do
  [[ -z "${cname}" ]] && continue
  dbu=$(db_url_for "${cname}")
  if [[ -z "${dbu}" ]]; then
    echo ">>> ${cname} (unknown db mapping, skip)"
    continue
  fi
  echo ""
  echo ">>> ${cname} <<<"
  docker exec "${cname}" freqtrade show-trades --db-url "${dbu}" 2>/dev/null | head -45 || echo "(exec failed or no trades)"
done < <(docker ps --filter "name=cointpairs" --format '{{.Names}}' | sort)

echo ""
echo "================================================================================"
echo "Done."
echo "================================================================================"
