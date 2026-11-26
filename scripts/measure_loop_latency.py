#!/usr/bin/env python3
"""Trigger an origin CollateralRatioAlert and measure full Reactive callback loop latency.

Sends `emitRiskAlert` on the origin chain, waits for receipt confirmation, then
polls `DestinationLiquidatorGuard` on the destination chain for the matching
`RebalanceExecuted` log and records wall-clock + block latency to
`docs/live_loop_evidence.json`.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from web3 import Web3


ORIGIN_ABI = [
    {
        "type": "function",
        "name": "emitRiskAlert",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "vaultId", "type": "uint256"},
            {"name": "owner", "type": "address"},
            {"name": "currentRatio", "type": "uint256"},
            {"name": "minRatio", "type": "uint256"},
            {"name": "recommendedAction", "type": "uint256"},
        ],
        "outputs": [],
    }
]

GUARD_ABI = [
    {
        "type": "event",
        "name": "RebalanceExecuted",
        "inputs": [
            {"name": "vaultId", "type": "uint256", "indexed": True},
            {"name": "owner", "type": "address", "indexed": True},
            {"name": "actionCode", "type": "uint256", "indexed": False},
            {"name": "timestamp", "type": "uint256", "indexed": False},
        ],
    },
    {
        "type": "function",
        "name": "totalRebalances",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"type": "uint256"}],
    },
]


def measure_live_loop(
    *,
    origin_rpc: str,
    dest_rpc: str,
    origin_addr: str,
    dest_addr: str,
    private_key: str,
    vault_id: int,
    current_ratio: int,
    min_ratio: int,
    action_code: int,
    timeout_seconds: float,
    output_path: Path,
) -> dict[str, object]:
    """Send origin alert tx and poll destination guard until callback lands."""
    w3_origin = Web3(Web3.HTTPProvider(origin_rpc))
    w3_dest = Web3(Web3.HTTPProvider(dest_rpc))
    acct = w3_origin.eth.account.from_key(private_key)

    origin = w3_origin.eth.contract(address=Web3.to_checksum_address(origin_addr), abi=ORIGIN_ABI)
    guard = w3_dest.eth.contract(address=Web3.to_checksum_address(dest_addr), abi=GUARD_ABI)

    dest_start_block = w3_dest.eth.block_number
    nonce = w3_origin.eth.get_transaction_count(acct.address)
    tx = origin.functions.emitRiskAlert(
        vault_id,
        acct.address,
        current_ratio,
        min_ratio,
        action_code,
    ).build_transaction(
        {
            "from": acct.address,
            "nonce": nonce,
            "chainId": w3_origin.eth.chain_id,
            "gas": 150000,
        }
    )
    signed = acct.sign_transaction(tx)
    t_send = time.perf_counter()
    origin_tx_hash = w3_origin.eth.send_raw_transaction(signed.raw_transaction).hex()
    origin_receipt = w3_origin.eth.wait_for_transaction_receipt(origin_tx_hash, timeout=120)
    origin_confirmed_s = time.perf_counter() - t_send

    deadline = time.perf_counter() + timeout_seconds
    callback_event = None
    dest_tx_hash = None
    dest_block = None

    while time.perf_counter() < deadline:
        events = guard.events.RebalanceExecuted.get_logs(
            from_block=dest_start_block,
            to_block="latest",
            argument_filters={"vaultId": vault_id},
        )
        if events:
            callback_event = events[-1]
            dest_tx_hash = callback_event["transactionHash"].hex()
            dest_block = callback_event["blockNumber"]
            break
        time.sleep(2.0)

    total_latency_s = time.perf_counter() - t_send
    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "origin_chain_id": w3_origin.eth.chain_id,
        "destination_chain_id": w3_dest.eth.chain_id,
        "origin_contract": Web3.to_checksum_address(origin_addr),
        "destination_contract": Web3.to_checksum_address(dest_addr),
        "vault_id": vault_id,
        "origin_tx_hash": origin_tx_hash,
        "origin_block": origin_receipt["blockNumber"],
        "origin_confirm_seconds": round(origin_confirmed_s, 3),
        "destination_tx_hash": dest_tx_hash,
        "destination_block": dest_block,
        "full_loop_latency_seconds": round(total_latency_s, 3) if dest_tx_hash else None,
        "callback_observed": dest_tx_hash is not None,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure origin -> Reactive -> destination callback latency")
    parser.add_argument("--vault-id", type=int, default=int(time.time()) % 100000)
    parser.add_argument("--current-ratio", type=int, default=11000)
    parser.add_argument("--min-ratio", type=int, default=12500)
    parser.add_argument("--action-code", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    parser.add_argument("--output", type=Path, default=Path("docs/live_loop_evidence.json"))
    args = parser.parse_args()

    required = ["PRIVATE_KEY", "ORIGIN_RPC_URL", "DEST_RPC_URL", "ORIGIN_CONTRACT", "DESTINATION_CONTRACT"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise SystemExit(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Populate .env from .env.example after funding your burner testnet wallet."
        )

    res = measure_live_loop(
        origin_rpc=os.environ["ORIGIN_RPC_URL"],
        dest_rpc=os.environ["DEST_RPC_URL"],
        origin_addr=os.environ["ORIGIN_CONTRACT"],
        dest_addr=os.environ["DESTINATION_CONTRACT"],
        private_key=os.environ["PRIVATE_KEY"],
        vault_id=args.vault_id,
        current_ratio=args.current_ratio,
        min_ratio=args.min_ratio,
        action_code=args.action_code,
        timeout_seconds=args.timeout_seconds,
        output_path=args.output,
    )
    print(json.dumps(res, indent=2))
    return 0 if res["callback_observed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
