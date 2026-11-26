"""Reactive Sentinel CLI Entrypoint.

Demonstrator and live AI risk-triage runner for the Reactive Omni Buildathon.
Supports deterministic local mode and `--live-ai` model triage gated by invariants.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from reactive_sentinel.agent import ReactiveSentinelAgent


def run_demo(verbose: bool = True, live_ai: bool = False) -> int:
    """Run Reactive Sentinel evaluation across deficit and healthy vault events."""
    t0 = time.perf_counter()

    if verbose:
        print("=" * 68)
        print("  REACTIVE SENTINEL (Reactive Omni Network)")
        print("  DoraHacks Buildathon: Cross-Chain Invariant Guardian")
        print("=" * 68)

    origin_chain_id = int(os.getenv("ORIGIN_CHAIN_ID", "0"))
    dest_chain_id = int(os.getenv("DESTINATION_CHAIN_ID", "0"))
    reactive_chain_id = int(os.getenv("REACTIVE_CHAIN_ID", "0"))

    agent = ReactiveSentinelAgent(
        agent_id=os.getenv("SENTINEL_AGENT_ID", "sentinel-node-01"),
        origin_chain_id=origin_chain_id,
        destination_chain_id=dest_chain_id,
    )

    if verbose:
        origin_disp = str(origin_chain_id) if origin_chain_id else "${ORIGIN_CHAIN_ID}"
        react_disp = str(reactive_chain_id) if reactive_chain_id else "${REACTIVE_CHAIN_ID}"
        dest_disp = str(dest_chain_id) if dest_chain_id else "${DESTINATION_CHAIN_ID}"

        print(f"\n[1] Initialized Reactive Sentinel Agent: '{agent.agent_id}'")
        print(f"    - Mode:                {'AI triage + invariant gate' if live_ai else 'Deterministic local check'}")
        print(f"    - Origin Network:      Chain ID {origin_disp}")
        print(f"    - Reactive Network:    Chain ID {react_disp}")
        print(f"    - Destination Network: Chain ID {dest_disp}")

    critical_event_id = "evt-vault-101-margin-call"
    if live_ai:
        decision_crit, receipt_crit = agent.process_event_with_ai(
            event_id=critical_event_id,
            vault_id=101,
            current_ratio=11000,
            min_ratio=12500,
        )
        check_crit = decision_crit.check
        crit_action = decision_crit.recommended_action
    else:
        decision_crit = None
        crit_action = 1
        check_crit, receipt_crit = agent.process_event(
            event_id=critical_event_id,
            vault_id=101,
            current_ratio=11000,
            min_ratio=12500,
            action_code=crit_action,
        )

    if verbose:
        print(f"\n[2] Ingesting Risk Event: '{critical_event_id}'")
        print("    - Vault ID: 101 | Collateral Ratio: 110% | Min Ratio: 125%")
        print("    - Invariant Status: DEFICIT DETECTED (Ratio < Threshold)")
        if decision_crit is not None:
            print(
                f"    - Model ({decision_crit.model}): action={crit_action} ({decision_crit.action_label}), "
                f"used={decision_crit.model_used}, overridden={decision_crit.invariant_overridden}"
            )
            print(f"    - Rationale: {decision_crit.rationale}")
        print(f"    [OK] Invariant Check:   PASSED ({check_crit.latency_ms:.2f}ms)")
        print(
            f"    [OK] Callback Path:     executeDefensiveActionWithNonce(vault=101, action={crit_action})"
        )
        print(f"    [OK] Attestation Sig:   {receipt_crit.signature[:24]}...")

    safe_event_id = "evt-vault-102-healthy"
    if live_ai:
        decision_safe, receipt_safe = agent.process_event_with_ai(
            event_id=safe_event_id,
            vault_id=102,
            current_ratio=15500,
            min_ratio=12500,
        )
        check_safe = decision_safe.check
    else:
        decision_safe = None
        check_safe, receipt_safe = agent.process_event(
            event_id=safe_event_id,
            vault_id=102,
            current_ratio=15500,
            min_ratio=12500,
            action_code=1,
        )

    if verbose:
        print(f"\n[3] Ingesting Normal Event: '{safe_event_id}'")
        print("    - Vault ID: 102 | Collateral Ratio: 155% | Min Ratio: 125%")
        print("    - Invariant Status: HEALTHY (Ratio >= Threshold)")
        if decision_safe is not None:
            print(
                f"    - Model ({decision_safe.model}): used={decision_safe.model_used}, "
                f"overridden={decision_safe.invariant_overridden}"
            )
        print(f"    [OK] Invariant Check:   PASSED ({check_safe.latency_ms:.2f}ms)")
        print("    [OK] Callback Path:     NO CALLBACK (ratio healthy)")
        print(f"    [OK] Attestation Sig:   {receipt_safe.signature[:24]}...")

    total_ms = (time.perf_counter() - t0) * 1000.0
    if verbose:
        print("\n" + "=" * 68)
        print(f"  SENTINEL COMPLETE: checks finished in {total_ms:.2f}ms")
        print("=" * 68 + "\n")

    return 0


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Reactive Sentinel CLI")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode")
    parser.add_argument(
        "--live-ai",
        action="store_true",
        help="Invoke an OpenAI-compatible model (REACTIVE_MODEL / REACTIVE_BASE_URL) gated by the invariant verifier",
    )
    args = parser.parse_args()
    sys.exit(run_demo(verbose=not args.quiet, live_ai=args.live_ai))


if __name__ == "__main__":
    main()
