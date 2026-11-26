"""The deployment evidence the README cites must match the committed Foundry receipt."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "broadcast" / "DeployOriginAndDestination.s.sol" / "84532" / "run-latest.json"
README = (ROOT / "README.md").read_text(encoding="utf-8")


def _receipt() -> dict:
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def test_receipt_records_both_base_sepolia_contracts() -> None:
    names = {t["contractName"]: t["contractAddress"] for t in _receipt()["transactions"]}
    assert set(names) == {"OriginRiskEmitter", "DestinationLiquidatorGuard"}
    assert _receipt()["chain"] == 84532


def test_every_deploy_succeeded_on_chain() -> None:
    data = _receipt()
    hashes = {t["hash"] for t in data["transactions"]}
    assert hashes == {r["transactionHash"] for r in data["receipts"]}
    assert all(r["status"] == "0x1" for r in data["receipts"])


def test_readme_cites_exactly_the_receipt_addresses_and_hashes() -> None:
    data = _receipt()
    for tx in data["transactions"]:
        assert tx["contractAddress"].lower() in README.lower()
        assert tx["hash"].lower() in README.lower()
