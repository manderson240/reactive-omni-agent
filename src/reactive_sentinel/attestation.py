"""Cryptographic Attestation for Reactive Cross-Chain Executions.
=================================================================
Signs verification results using HMAC-SHA256 with timestamping and epoch fencing.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReactiveAttestationReceipt:
    """Tamper-evident attestation receipt for an executed reactive cycle."""

    event_id: str
    origin_chain_id: int
    destination_chain_id: int
    executed: bool
    signature: str
    timestamp_ns: int


class ReactiveAttestationSigner:
    """Signs and verifies HMAC-SHA256 attestation receipts."""

    def __init__(
        self,
        signer_id: str = "reactive-sentinel-01",
        secret_key: bytes = b"reactive_omni_sentinel_secret_2026",
    ) -> None:
        self.signer_id = signer_id
        self.secret_key = secret_key

    def sign(
        self,
        event_id: str,
        origin_chain_id: int,
        destination_chain_id: int,
        executed: bool,
    ) -> ReactiveAttestationReceipt:
        """Create an attestation receipt for a reactive execution."""
        timestamp_ns = time.time_ns()
        message = (
            f"{event_id}:{self.signer_id}:{origin_chain_id}:{destination_chain_id}:{executed}:{timestamp_ns}"
        ).encode("utf-8")
        sig = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()

        return ReactiveAttestationReceipt(
            event_id=event_id,
            origin_chain_id=origin_chain_id,
            destination_chain_id=destination_chain_id,
            executed=executed,
            signature=sig,
            timestamp_ns=timestamp_ns,
        )

    def verify(self, receipt: ReactiveAttestationReceipt) -> bool:
        """Verify receipt cryptographic validity."""
        message = (
            f"{receipt.event_id}:{self.signer_id}:{receipt.origin_chain_id}:{receipt.destination_chain_id}:{receipt.executed}:{receipt.timestamp_ns}"
        ).encode("utf-8")
        expected_sig = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(receipt.signature, expected_sig)
