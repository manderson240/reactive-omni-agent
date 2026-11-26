"""AI Risk Triage Client with Deterministic Invariant Override.

Supports Track 3 ("Reactive Meets AI") by asking a live OpenAI-compatible
model (Ollama local/cloud or hosted API) to classify defensive action type
and rationale for a vault event, then running the result through
`verify_risk_event` so a confused or malformed model output cannot suppress
a required liquidation protection callback or fire on a healthy vault.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from reactive_sentinel.verifier import InvariantCheckResult, verify_risk_event


VALID_ACTIONS: dict[int, str] = {
    1: "RepayDebt",
    2: "SupplyCollateral",
}


@dataclass(slots=True)
class AITriageDecision:
    """Structured triage decision combining model recommendation and invariant guard."""

    model: str
    recommended_action: int
    action_label: str
    rationale: str
    model_used: bool
    invariant_overridden: bool
    check: InvariantCheckResult


def _extract_json_object(text: str) -> dict[str, Any]:
    """Parse JSON object from plain or fenced model output."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1]).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    obj = json.loads(cleaned)
    if not isinstance(obj, dict):
        raise ValueError("Expected JSON object from triage model")
    return obj


def _default_heuristic_action(current_ratio: int, min_ratio: int) -> int:
    """Deterministic fallback action selection when model output is unusable."""
    # Deeply under-collateralized vaults favor immediate debt repayment (1);
    # mild deficits favor collateral top-up (2).
    if current_ratio + 1500 <= min_ratio:
        return 1
    return 2 if current_ratio < min_ratio else 1


def triage_risk_event_with_model(
    *,
    vault_id: int,
    current_ratio: int,
    min_ratio: int,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout_seconds: float = 30.0,
) -> AITriageDecision:
    """Ask a model for action selection and enforce safety invariants on its answer."""
    resolved_model = model or os.getenv("REACTIVE_MODEL", "deepseek-v4.1-flash:cloud")
    resolved_url = (base_url or os.getenv("REACTIVE_BASE_URL", "http://127.0.0.1:11434/v1")).rstrip("/")
    resolved_key = api_key or os.getenv("REACTIVE_API_KEY", "local")

    system_msg = (
        "You triage DeFi lending vault collateral events. Respond with ONLY valid JSON "
        'matching {"recommended_action": 1 or 2, "trigger_callback": true or false, '
        '"rationale": "one short plain sentence"}. Action 1 is RepayDebt, action 2 is '
        "SupplyCollateral."
    )
    user_msg = (
        f"Vault {vault_id}: current_ratio={current_ratio} bps, min_ratio={min_ratio} bps. "
        "Choose action 1 or 2 and whether a callback should run."
    )
    payload = json.dumps(
        {
            "model": resolved_model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{resolved_url}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {resolved_key}",
        },
        method="POST",
    )

    fallback_action = _default_heuristic_action(current_ratio, min_ratio)
    chosen_action = fallback_action
    rationale = ""
    model_used = False
    overridden = False
    model_trigger_claim: bool | None = None

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        content = raw["choices"][0]["message"]["content"]
        parsed = _extract_json_object(content)
        raw_action = parsed.get("recommended_action")
        if isinstance(raw_action, int) and raw_action in VALID_ACTIONS:
            chosen_action = raw_action
        else:
            overridden = True
        if isinstance(parsed.get("trigger_callback"), bool):
            model_trigger_claim = parsed["trigger_callback"]
        rationale = str(parsed.get("rationale", "")).strip()[:240]
        model_used = True
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        rationale = f"Fallback heuristic used after model failure: {exc}"
        overridden = True

    check = verify_risk_event(
        vault_id=vault_id,
        current_ratio=current_ratio,
        min_ratio=min_ratio,
        action_code=chosen_action,
    )
    if model_trigger_claim is not None and model_trigger_claim != check.requires_callback:
        overridden = True
        rationale = (
            f"Invariant override: model claimed trigger={model_trigger_claim}, "
            f"deterministic ratio gate requires {check.requires_callback}. {rationale}"
        ).strip()

    if not rationale:
        rationale = f"Selected {VALID_ACTIONS[chosen_action]} for vault {vault_id}."

    return AITriageDecision(
        model=resolved_model,
        recommended_action=chosen_action,
        action_label=VALID_ACTIONS[chosen_action],
        rationale=rationale,
        model_used=model_used,
        invariant_overridden=overridden,
        check=check,
    )
