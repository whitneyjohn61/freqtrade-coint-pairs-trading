# Forward experiment charter — Candidate L (deploy repo)

This file aligns **`freqtrade-coint-pairs-trading`** with **`AlgoTrading_Research_Log.md` v5.0** in the companion repo **`freqtrade-strategy-lab`** (`user_data/info/AlgoTrading_Research_Log.md`). That log is the source of truth for gates §6.1–§6.6; this repo does not duplicate it.

## What this deployment is

- **Bounded forward / operations rehearsal** for **Enhanced Cointegration Pairs** (Candidate L): three spreads (BTC/ETH, BNB/SOL, BTC/SOL) × **V01 vs V02** replicas on two hosts (six Freqtrade processes).
- **Portfolio-scale activity** is the relevant unit for the Research Log’s §2 objective (individual bots may trade slowly).

## What this deployment is not

- **Not** a claim that Candidate L **cleared** v5.0 **§6** (buildability + **edge deflation** + paper replication + Phase 0 economics). Those steps are tracked in the Research Log; **deflation pass on L** is explicitly sequenced there (§4.6).
- **Not** a replication of Palazzi-style **headline** metrics (best-of-pair-universe, pre-publication Sharpe, etc.). The three spreads here are a **small, hand-picked** set — interpret results with **selection bias** in mind.

## Scope freeze (until Research Log is updated)

Without a written decision in **`AlgoTrading_Research_Log.md`** (and ideally a session note):

- **Do not** add new **compose profiles**, new **droplet processes**, or new **production spreads** beyond the three configs already in `docker-compose.yml`.
- **Do not** treat exploratory configs (`link_eth`, `uni_sol`, `xmr_btc`, etc.) as droplet-bound unless the Dev Plan / log explicitly promotes them after §6-style review.

Expanding scope belongs after **§4.6 step 4** (deflation pass on L) and a clear choice: **standalone portfolio-of-pairs**, **GatedExecution signal layer**, or **shelve**.

## Pre-registered read criteria (guidance)

Aligned with Research Log **§2** (forward-testing realism):

| Milestone | Use |
|-----------|-----|
| **≥ ~50 closed trades** (portfolio-wide across all six DBs, or per-sleeve if deciding sleeves independently) | Coarse **go / no-go / continue** read |
| **≥ ~150 closed trades** | Sharpe / confidence-interval style read |
| Regime or **calendar-year splits** | Required before declaring **edge** vs **beta** or one-off luck |

## Formal checkpoints

Snapshot source: `scripts/droplet_combined_summary_from_local.py` (SSH to both droplets, all six containers). Total PnL = closed (`close_profit_abs`) + open legs (live `/api/v1/status` MTM). % = total PnL / sum(`stake_amount`) per instance DB.

### 2026-04-18

| Level | Open legs | Closed legs | Open MTM (USDT) | Total PnL (USDT) | Total %PnL |
|-------|-----------|-------------|-----------------|-----------------|------------|
| **All six DBs** | 8 | 12 | ~82.9 | ~−774.2 | ~−1.72% |

| Sleeve (×2 replicas) | Total PnL (USDT) approx. | Notes |
|----------------------|---------------------------|--------|
| BTC/ETH (8080 / 8083) | ~+123 / ~+122 | Both replicas net positive on DB + open MTM. |
| BNB/SOL (8081 / 8084) | ~−105 / ~−102 | Both replicas net negative. |
| BTC/SOL (8082 / 8085) | ~−403 / ~−408 | **No open trades**; losses are **realized** on closed legs only. |

**Outcome:** **CONTINUE** — **12** closed trades portfolio-wide is **below** the ~**50** closed-trade bar (Research Log §2) for a coarse go/no-go; aggregate economics still **negative**. Infra: all six containers **Up** (~2 weeks uptime in snapshot). **§6 status unchanged** (not a “pass”). **BTC/SOL:** losses remain **sleeve-dominant**; next checkpoint either adopt a **pre-registered pause/downsize rule** for that sleeve or document why both replicas stay at full risk.

**Last review:** **2026-04-18** — **CONTINUE** (see table above).

## Per-sleeve policy

- **BTC/ETH** and **BNB/SOL:** default **continue** under charter until review milestones; treat PnL as **hypothesis data**, not proof.
- **BTC/SOL:** if realized losses remain dominant vs other sleeves, **pause or reduce risk** on that sleeve only after documenting a **pre-registered rule** (e.g. “pause if X by date Y”) in this file or the Research Log — avoid purely narrative cutoffs.

## Artifacts

- **Local status (all six instances):** `scripts/droplet_status_from_local.ps1` (combined summary + all-trades table when Python helpers are present).
- **Candidate L narrative:** `user_data/info/EnhancedCointPairs_Deep_Dive.md`
- **Dev plan (copy):** `user_data/info/EnhancedCointPairs_Dev_Plan.md` — canonical long-form plan may live in **strategy-lab**; keep charter vs implementation distinct.

## Related v5.0 sections (read in strategy-lab log)

- **§4.4** — Candidate L status, reframing, deferral to GatedExecution design.
- **§4.6** — Priority sequencing (deflation pass on L before major new builds).
- **§6.2** — Edge Deflation Pass (fees, Sharpe decay, slippage).
