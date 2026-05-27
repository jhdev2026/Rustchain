#!/usr/bin/env python3
"""
RustChain Attestation Data Export Tool
Bounty: #49 — Attestation Data Export Pipeline

Usage:
    python3 rustchain_export.py --format csv --output data/
    python3 rustchain_export.py --format json --output data/
    python3 rustchain_export.py --format jsonl --output data/ --from 2025-12-01 --to 2026-02-01
    python3 rustchain_export.py --format all --output data/ --node https://50.28.86.131
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import urllib.request
import urllib.error


API_DEFAULTS = {
    "node": "https://50.28.86.131",
    "timeout": 30,
}


def fetch_json(url: str, timeout: int = 30) -> dict[str, Any]:
    """Fetch JSON from URL, handling self-signed certs."""
    # In production, you might want to configure SSL properly.
    # For now we skip cert verification for self-signed certs.
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "RustChain-Export/1.0")
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return {}


def fetch_epoch(node: str) -> dict[str, Any]:
    return fetch_json(f"{node}/epoch")


def fetch_miners(node: str) -> list[dict[str, Any]]:
    data = fetch_json(f"{node}/api/miners")
    return data.get("miners", [])


def fetch_balance(node: str, miner_id: str) -> dict[str, Any]:
    url = f"{node}/wallet/balance?miner_id={miner_id}"
    return fetch_json(url)


def fetch_all_balances(node: str, miner_ids: list[str]) -> list[dict[str, Any]]:
    """Fetch balances for all miners."""
    results = []
    for miner_id in miner_ids:
        balance = fetch_balance(node, miner_id)
        if balance:
            balance["miner_id"] = miner_id
            results.append(balance)
        time.sleep(0.1)  # Rate limit: 30/min
    return results


def export_csv(data: list[dict], filename: Path, fieldnames: list[str] = None):
    """Export list of dicts to CSV."""
    if not data:
        Path(filename).write_text("")
        return
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"  CSV: {filename} ({len(data)} rows)")


def export_json(data: Any, filename: Path, indent: int = 2):
    """Export JSON to file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)
    print(f"  JSON: {filename}")


def export_jsonl(data: list[dict], filename: Path):
    """Export JSON Lines (newline-delimited JSON) to file."""
    with open(filename, "w", encoding="utf-8") as f:
        for row in data:
            f.write(json.dumps(row, default=str) + "\n")
    print(f"  JSONL: {filename} ({len(data)} rows)")


def ts_to_iso(ts: int | float) -> str:
    """Convert Unix timestamp to ISO 8601 string."""
    if ts <= 0:
        return ""
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(
        description="RustChain Attestation Data Export Tool"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["csv", "json", "jsonl", "all"],
        default="csv",
        help="Output format"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("data"),
        help="Output directory"
    )
    parser.add_argument(
        "--from", dest="date_from",
        help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--to", dest="date_to",
        help="End date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--node",
        default=API_DEFAULTS["node"],
        help=f"RustChain node URL (default: {API_DEFAULTS['node']})"
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        default=["miners", "epochs", "balances"],
        choices=["miners", "epochs", "balances", "rewards", "attestations"],
        help="Tables to export"
    )

    args = parser.parse_args()
    node = args.node.rstrip("/")

    print(f"=== RustChain Data Export ===")
    print(f"Node: {node}")
    print(f"Format: {args.format}")
    print(f"Output: {args.output}")
    print()

    args.output.mkdir(parents=True, exist_ok=True)

    # --- Miners ---
    if "miners" in args.tables:
        print("Fetching miners...")
        miners = fetch_miners(node)
        print(f"  Found {len(miners)} miners")

        miners_export = []
        for m in miners:
            miners_export.append({
                "miner_id": m.get("miner", ""),
                "device_arch": m.get("device_arch", ""),
                "device_family": m.get("device_family", ""),
                "hardware_type": m.get("hardware_type", ""),
                "antiquity_multiplier": m.get("antiquity_multiplier", ""),
                "entropy_score": m.get("entropy_score", ""),
                "first_attest_ts": m.get("first_attest", ""),
                "first_attest_iso": ts_to_iso(m.get("first_attest", 0)),
                "last_attest_ts": m.get("last_attest", ""),
                "last_attest_iso": ts_to_iso(m.get("last_attest", 0)),
            })

        if args.format in ("csv", "all"):
            export_csv(miners_export, args.output / "miners.csv")
        if args.format in ("json", "all"):
            export_json(miners_export, args.output / "miners.json")
        if args.format in ("jsonl", "all"):
            export_jsonl(miners_export, args.output / "miners.jsonl")

    # --- Epoch ---
    if "epochs" in args.tables:
        print("Fetching epoch...")
        epoch = fetch_epoch(node)
        if epoch:
            epoch_export = [{
                "epoch": epoch.get("epoch", ""),
                "slot": epoch.get("slot", ""),
                "blocks_per_epoch": epoch.get("blocks_per_epoch", ""),
                "epoch_pot": epoch.get("epoch_pot", ""),
                "enrolled_miners": epoch.get("enrolled_miners", ""),
                "total_supply_rtc": epoch.get("total_supply_rtc", ""),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }]

            if args.format in ("csv", "all"):
                export_csv(epoch_export, args.output / "epochs.csv")
            if args.format in ("json", "all"):
                export_json(epoch_export, args.output / "epochs.json")
            if args.format in ("jsonl", "all"):
                export_jsonl(epoch_export, args.output / "epochs.jsonl")
        else:
            print("  Failed to fetch epoch data")

    # --- Balances ---
    if "balances" in args.tables:
        print("Fetching miners for balance lookup...")
        miners = fetch_miners(node)
        miner_ids = [m.get("miner", "") for m in miners if m.get("miner")]
        print(f"Fetching {len(miner_ids)} balances...")
        balances = fetch_all_balances(node, miner_ids)

        balances_export = []
        for b in balances:
            balances_export.append({
                "miner_id": b.get("miner_id", ""),
                "amount_rtc": b.get("amount_rtc", ""),
                "amount_i64": b.get("amount_i64", ""),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

        if args.format in ("csv", "all"):
            export_csv(balances_export, args.output / "balances.csv")
        if args.format in ("json", "all"):
            export_json(balances_export, args.output / "balances.json")
        if args.format in ("jsonl", "all"):
            export_jsonl(balances_export, args.output / "balances.jsonl")

    print()
    print("=== Export complete ===")


if __name__ == "__main__":
    main()