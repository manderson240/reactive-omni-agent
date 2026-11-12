"""Unit tests for Reactive Sentinel Python Agent."""

from __future__ import annotations

from reactive_sentinel.agent import ReactiveSentinelAgent
from reactive_sentinel.attestation import ReactiveAttestationSigner
from reactive_sentinel.verifier import verify_risk_event


def test_verify_risk_event_triggers_when_under_threshold() -> None:
    res = verify_risk_event(vault_id=101, current_ratio=11000, min_ratio=12500, action_code=1)
    assert res.valid is True
    assert res.requires_callback is True
    assert len(res.violations) == 0


def test_verify_risk_event_ignores_when_above_threshold() -> None:
    res = verify_risk_event(vault_id=102, current_ratio=15000, min_ratio=12500, action_code=1)
    assert res.valid is True
    assert res.requires_callback is False
    assert len(res.violations) == 0


def test_verify_risk_event_rejects_invalid_action_code() -> None:
    res = verify_risk_event(vault_id=103, current_ratio=11000, min_ratio=12500, action_code=99)
    assert res.valid is False
    assert res.requires_callback is False
    assert any("Invalid action_code" in v for v in res.violations)


def test_attestation_signing_and_verification() -> None:
    signer = ReactiveAttestationSigner(signer_id="test-signer-01")
    receipt = signer.sign(
        event_id="evt-test-1",
        origin_chain_id=84532,
        destination_chain_id=84532,
        executed=True,
    )
    assert receipt.event_id == "evt-test-1"
    assert receipt.executed is True
    assert len(receipt.signature) == 64
    assert signer.verify(receipt) is True


def test_agent_end_to_end_processing() -> None:
    agent = ReactiveSentinelAgent(agent_id="test-agent")
    check, receipt = agent.process_event(
        event_id="evt-101",
        vault_id=101,
        current_ratio=10500,
        min_ratio=12000,
        action_code=2,
    )
    assert check.valid is True
    assert check.requires_callback is True
    assert receipt.executed is True
    assert agent.signer.verify(receipt) is True
