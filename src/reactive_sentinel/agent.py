"""Reactive Sentinel AI Agent.

Autonomous monitor that evaluates cross-chain DeFi risk events, executes
deterministic invariant checks, and coordinates Reactive Omni callbacks.
"""

from __future__ import annotations

import os
from typing import Any

from reactive_sentinel.attestation import ReactiveAttestationReceipt, ReactiveAttestationSigner
from reactive_sentinel.model_triage import AITriageDecision, triage_risk_event_with_model
from reactive_sentinel.verifier import InvariantCheckResult, verify_risk_event


class ReactiveSentinelAgent:
    """Coordinates event observation, invariant verification, AI triage, and attestation."""

    def __init__(
        self,
        agent_id: str | None = None,
        origin_chain_id: int | None = None,
        destination_chain_id: int | None = None,
    ) -> None:
        self.agent_id = agent_id or os.getenv("SENTINEL_AGENT_ID", "reactive-sentinel-node-01")

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
        """Process an observed DeFi risk event through the deterministic sentinel pipeline."""
        check = verify_risk_event(
            vault_id=vault_id,
            current_ratio=current_ratio,
            min_ratio=min_ratio,
            action_code=action_code,
        )

        receipt = self.signer.sign(
            event_id=event_id,
            origin_chain_id=self.origin_chain_id,
            destination_chain_id=self.destination_chain_id,
            executed=check.requires_callback,
        )

        return check, receipt

    def process_event_with_ai(
        self,
        *,
        event_id: str,
        vault_id: int,
        current_ratio: int,
        min_ratio: int,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> tuple[AITriageDecision, ReactiveAttestationReceipt]:
        """Run AI model triage and gate its output through the deterministic verifier."""
        decision = triage_risk_event_with_model(
            vault_id=vault_id,
            current_ratio=current_ratio,
            min_ratio=min_ratio,
            model=model,
            base_url=base_url,
            api_key=api_key,
        )
        receipt = self.signer.sign(
            event_id=event_id,
            origin_chain_id=self.origin_chain_id,
            destination_chain_id=self.destination_chain_id,
            executed=decision.check.requires_callback,
        )
        return decision, receipt
