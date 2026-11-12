"""Reactive Sentinel AI Agent.
=============================
Autonomous monitor that evaluates cross-chain DeFi risk events, executes
deterministic invariant checks, and coordinates Reactive Omni callbacks.
"""

from __future__ import annotations

import os
from typing import Any

from reactive_sentinel.attestation import ReactiveAttestationReceipt, ReactiveAttestationSigner
from reactive_sentinel.verifier import InvariantCheckResult, verify_risk_event


class ReactiveSentinelAgent:
    """Coordinates event observation, invariant verification, and attestation."""

    def __init__(
        self,
        agent_id: str | None = None,
        origin_chain_id: int | None = None,
        destination_chain_id: int | None = None,
    ) -> None:
        self.agent_id = agent_id or os.getenv("SENTINEL_AGENT_ID", "reactive-sentinel-node-01")

        # Dynamic variable resolution - sensitive chain IDs are loaded from environment / vault
        if origin_chain_id is not None:
            self.origin_chain_id = origin_chain_id
        else:
            env_val = os.getenv("ORIGIN_CHAIN_ID")
            self.origin_chain_id = int(env_val) if env_val else 0

        if destination_chain_id is not None:
            self.destination_chain_id = destination_chain_id
        else:
            env_val = os.getenv("DESTINATION_CHAIN_ID")
            self.destination_chain_id = int(env_val) if env_val else 0

        self.signer = ReactiveAttestationSigner(signer_id=self.agent_id)

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
