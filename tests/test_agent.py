"""Unit tests for Reactive Sentinel Python Agent and AI triage gate."""

from __future__ import annotations

import io
import json
from typing import Any

from reactive_sentinel.agent import ReactiveSentinelAgent
from reactive_sentinel.attestation import ReactiveAttestationSigner
from reactive_sentinel.model_triage import triage_risk_event_with_model
from reactive_sentinel.verifier import verify_risk_event


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


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
        origin_chain_id=1001,
        destination_chain_id=1001,
        executed=True,
    )
    assert receipt.event_id == "evt-test-1"
    assert receipt.executed is True
    assert len(receipt.signature) == 64
    assert signer.verify(receipt) is True


def test_agent_dynamic_environment_chain_ids(monkeypatch) -> None:
    monkeypatch.setenv("ORIGIN_CHAIN_ID", "42001")
    monkeypatch.setenv("DESTINATION_CHAIN_ID", "42002")
    agent = ReactiveSentinelAgent(agent_id="test-env-agent")
    assert agent.origin_chain_id == 42001
    assert agent.destination_chain_id == 42002


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


def test_ai_triage_accepts_valid_model_choice(monkeypatch) -> None:
    def fake_urlopen(req: Any, timeout: float = 30.0) -> _FakeResponse:
        return _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "recommended_action": 2,
                                    "trigger_callback": True,
                                    "rationale": "Moderate collateral shortfall fits top-up.",
                                }
                            )
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("reactive_sentinel.model_triage.urllib.request.urlopen", fake_urlopen)
    decision = triage_risk_event_with_model(
        vault_id=101,
        current_ratio=11200,
        min_ratio=12500,
        model="fake-model",
    )
    assert decision.model_used is True
    assert decision.invariant_overridden is False
    assert decision.recommended_action == 2
    assert decision.check.requires_callback is True


def test_ai_triage_overrides_wrong_trigger_claim(monkeypatch) -> None:
    # Model wrongly tells sentinel NOT to trigger on an under-collateralized vault.
    def fake_urlopen(req: Any, timeout: float = 30.0) -> _FakeResponse:
        return _FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "recommended_action": 1,
                                    "trigger_callback": False,
                                    "rationale": "Looks fine to wait.",
                                }
                            )
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("reactive_sentinel.model_triage.urllib.request.urlopen", fake_urlopen)
    agent = ReactiveSentinelAgent(agent_id="test-ai-agent")
    decision, receipt = agent.process_event_with_ai(
        event_id="evt-override",
        vault_id=101,
        current_ratio=10500,
        min_ratio=12500,
        model="fake-model",
    )
    assert decision.model_used is True
    assert decision.invariant_overridden is True
    assert decision.check.requires_callback is True
    assert receipt.executed is True


def test_ai_triage_fallback_on_network_or_json_error(monkeypatch) -> None:
    def failing_urlopen(req: Any, timeout: float = 30.0) -> Any:
        raise ValueError("simulated malformed response")

    monkeypatch.setattr("reactive_sentinel.model_triage.urllib.request.urlopen", failing_urlopen)
    decision = triage_risk_event_with_model(
        vault_id=105,
        current_ratio=9800,
        min_ratio=12500,
        model="fake-model",
    )
    assert decision.model_used is False
    assert decision.invariant_overridden is True
    assert decision.recommended_action == 1
    assert decision.check.requires_callback is True
