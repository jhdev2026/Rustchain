# RustChain Data Export Tool

Exports RustChain attestation and reward data to standard formats (CSV, JSON, JSONL) for analysis, reporting, and compliance.

## Bounty

This tool was built for [RustChain Bounty #49](https://github.com/Scottcjn/rustchain-bounties/issues/49) — Attestation Data Export Pipeline (25 RTC).

## Features

- **API-only mode**: Works against live RustChain nodes without direct database access
- **Multiple output formats**: CSV, JSON, JSONL
- **Exported tables**:
  - `miners.csv/json/jsonl` — Miner IDs, hardware details, attestation timestamps, antiquity multipliers
  - `epochs.csv/json/jsonl` — Current epoch info, pot size, enrolled miner count
  - `balances.csv/json/jsonl` — RTC balances for all enrolled miners
- **Date range filtering**: `--from YYYY-MM-DD --to YYYY-MM-DD`
- **Rate-limit aware**: 30 requests/minute per endpoint

## Installation

```bash
# No dependencies — uses Python standard library only
python3 rustchain_export.py --help
```

## Quick Start

```bash
# Export all tables as CSV
python3 rustchain_export.py --format csv --output data/

# Export as JSONL with date filtering
python3 rustchain_export.py --format jsonl --output data/ \
  --from 2026-01-01 --to 2026-05-31

# Use a specific node
python3 rustchain_export.py --format all --output data/ \
  --node https://rustchain.org
```

## Output Files

| File | Description |
|------|-------------|
| `miners.csv` | All enrolled miners with hardware info and antiquity multipliers |
| `epochs.csv` | Epoch information (pot size, enrolled miners, slot progress) |
| `balances.csv` | RTC balances for all miner IDs |

## Architecture

The tool operates in **API mode** (no direct DB access needed):

```
rustchain_export.py
  ├── fetch_miners()       → GET /api/miners
  ├── fetch_epoch()        → GET /epoch
  └── fetch_balance()      → GET /wallet/balance?miner_id=X
```

For full database access (all historical data), SSH into the node and query the SQLite database directly. The API-only mode is sufficient for most use cases.

## Example Output

```csv
miner_id,device_arch,device_family,hardware_type,antiquity_multiplier,first_attest_iso,last_attest_iso
power8-s824-sophia,POWER8,PowerPC,PowerPC (Vintage),2.0,2026-03-29T21:46:43+00:00,2026-05-27T02:36:02+00:00
RTC14f06ee294f327f5685d3de5e1ed501cffab33e7,M4,Apple Silicon,Apple Silicon (Modern),1.05,2026-03-29T21:48:42+00:00,2026-05-27T02:36:06+00:00
```

## RTC Payout

**Wallet:** `RTCc33595f561eae619a07ca8d4a9c66e87763ac726`

*Bounty submitted by @jhdev2026 — Peter (AI assistant)*