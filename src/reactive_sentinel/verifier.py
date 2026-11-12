"""Deterministic Invariant and Safety Verifier.
==============================================
Validates cross-chain event logs and defensive action parameters before execution.
Runs in <0.1ms with 0 LLM tokens.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


# Permitted defensive action codes
VALID_ACTION_CODES = frozenset({1, 2, 3})  # 1 = RepayDebt, 2 = SupplyCollateral, 3 = RebalancePair


@dataclass(frozen=True, slots=True)
class InvariantCheckResult:
    """Outcome of static invariant check on a reactive event."""

    valid: bool
    requires_callback: bool
    violations: tuple[str, ...] = field(default_factory=tuple)
    latency_ms: float = 0.0


def verify_risk_event(
    vault_id: int,
    current_ratio: int,
    min_ratio: int,
    action_code: int,
) -> InvariantCheckResult:
    """Verify DeFi risk event parameters against protocol safety invariants.

    Parameters
    ----------
    vault_id : int
        Vault unique identifier.
    current_ratio : int
        Current collateral ratio in basis points (e.g. 11000 = 110%).
    min_ratio : int
        Liquidation threshold in basis points (e.g. 12500 = 125%).
    action_code : int
        Action code intended for the destination callback.

    Returns
    -------
    InvariantCheckResult
        Validation result with violation details and callback recommendation.
    """
    t0 = time.perf_counter()
    violations: list[str] = []

    if vault_id <= 0:
        violations.append(f"Invalid vault_id: {vault_id} must be positive.")

    if current_ratio <= 0:
        violations.append(f"Invalid current_ratio: {current_ratio} must be positive.")

    if min_ratio <= 0:
        violations.append(f"Invalid min_ratio: {min_ratio} must be positive.")

    if action_code not in VALID_ACTION_CODES:
        violations.append(f"Invalid action_code: {action_code}. Allowed: {sorted(VALID_ACTION_CODES)}.")

    dt_ms = (time.perf_counter() - t0) * 1000.0

    if violations:
        return InvariantCheckResult(
            valid=False,
            requires_callback=False,
            violations=tuple(violations),
            latency_ms=dt_ms,
        )

    # Invariant condition: trigger callback only if current_ratio < min_ratio
    needs_callback = current_ratio < min_ratio
    return InvariantCheckResult(
        valid=True,
        requires_callback=needs_callback,
        violations=(),
        latency_ms=dt_ms,
    )
