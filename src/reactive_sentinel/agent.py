"""Reactive Sentinel AI Agent.
=============================
Autonomous monitor that evaluates cross-chain DeFi risk events, executes
deterministic invariant checks, and coordinates Reactive Omni callbacks.
"""

from __future__ import annotations

from typing import Any

from reactive_sentinel.attestation import ReactiveAttestationReceipt, ReactiveAttestationSigner
from reactive_sentinel.verifier import InvariantCheckResult, verify_risk_event


class ReactiveSentinelAgent:
    """Coordinates event observation, invariant verification, and attestation."""

    def __init__(
        self,
        agent_id: str = "reactive-sentinel-node-01",
        origin_chain_id: int = 84532,       # Base Sepolia
        destination_chain_id: int = 84532,  # Base Sepolia
    ) -> None:
        self.agent_id = agent_id
        self.origin_chain_id = origin_chain_id
        self.destination_chain_id = destination_chain_id
        self.signer = ReactiveAttestationSigner(signer_id=agent_id)

    def process_event(
        self,
        event_id: str,
        vault_id: int,
        current_ratio: int,
        min_ratio: int,
        action_code: int,
    ) -> tuple[InvariantCheckResult, ReactiveAttestationReceipt]:
        """Process an observed DeFi risk event through the sentinel pipeline."""
        # 1. Deterministic invariant verification (0 tokens, <0.1ms)
        check = verify_risk_event(
            vault_id=vault_id,
            current_ratio=current_ratio,
            min_ratio=min_ratio,
            action_code=action_code,
        )

        # 2. Cryptographic attestation receipt
        receipt = self.signer.sign(
            event_id=event_id,
            origin_chain_id=self.origin_chain_id,
            destination_chain_id=self.destination_chain_id,
            executed=check.requires_callback,
        )

        return check, receipt
