#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.foundry/bin:$PATH"

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
  chmod 600 .env
fi

for var in PRIVATE_KEY ORIGIN_RPC_URL DEST_RPC_URL REACTIVE_LASNA_RPC_URL ORIGIN_CHAIN_ID DESTINATION_CHAIN_ID CALLBACK_RELAYER; do
  if [[ -z "${!var:-}" ]]; then
    echo "ERROR: $var is unset. Fill .env from .env.example before running." >&2
    exit 1
  fi
done

BURNER_ADDR="$(cast wallet address --private-key "$PRIVATE_KEY")"
echo "Using burner address: $BURNER_ADDR"

ORIGIN_BAL="$(cast balance "$BURNER_ADDR" --rpc-url "$ORIGIN_RPC_URL")"
if python3 -c "import sys; sys.exit(0 if int(sys.argv[1]) > 0 else 1)" "$ORIGIN_BAL"; then
  echo "Base Sepolia balance wei: $ORIGIN_BAL"
else
  echo "ERROR: Burner $BURNER_ADDR has 0 Base Sepolia ETH on $ORIGIN_RPC_URL." >&2
  echo "Fund $BURNER_ADDR with ~0.05 Base Sepolia ETH first via https://portal.cdp.coinbase.com (Onchain Tools -> Faucet), then re-run." >&2
  exit 1
fi

LASNA_CHAIN="${REACTIVE_CHAIN_ID:-5318007}"
FAUCET_CONTRACT="${REACTIVE_FAUCET_CONTRACT:-0x2afaFD298b23b62760711756088F75B7409f5967}"
LASNA_SWAP_ETH="${LASNA_SWAP_ETH:-0.02ether}"
LASNA_BAL="$(cast balance "$BURNER_ADDR" --rpc-url "$REACTIVE_LASNA_RPC_URL")"
if python3 -c "import sys; sys.exit(0 if int(sys.argv[1]) < 100000000000000000 else 1)" "$LASNA_BAL"; then
  echo "Lasna balance low ($LASNA_BAL wei); requesting lREACT via Base Sepolia faucet ($FAUCET_CONTRACT) with value=$LASNA_SWAP_ETH..."
  cast send "$FAUCET_CONTRACT" "request(address)" "$BURNER_ADDR" \
    --value "$LASNA_SWAP_ETH" \
    --rpc-url "$ORIGIN_RPC_URL" \
    --private-key "$PRIVATE_KEY"
  for _ in $(seq 1 12); do
    LASNA_BAL="$(cast balance "$BURNER_ADDR" --rpc-url "$REACTIVE_LASNA_RPC_URL")"
    if python3 -c "import sys; sys.exit(0 if int(sys.argv[1]) >= 100000000000000000 else 1)" "$LASNA_BAL"; then
      break
    fi
    sleep 3
  done
fi
if python3 -c "import sys; sys.exit(0 if int(sys.argv[1]) < 60000000000000000 else 1)" "$LASNA_BAL"; then
  echo "ERROR: Lasna lREACT balance still insufficient ($LASNA_BAL wei)." >&2
  exit 1
fi
echo "Reactive Lasna balance wei: $LASNA_BAL"

_update_env_var() {
  python3 - "$1" "$2" <<'PY'
import sys
from pathlib import Path

key, val = sys.argv[1], sys.argv[2]
p = Path(".env")
lines = p.read_text(encoding="utf-8").splitlines() if p.exists() else []
out = []
replaced = False
for line in lines:
    stripped = line.strip()
    if stripped.startswith(f"{key}=") or stripped.startswith(f"export {key}="):
        prefix = "export " if stripped.startswith("export ") else ""
        out.append(f"{prefix}{key}={val}")
        replaced = True
    else:
        out.append(line)
if not replaced:
    out.append(f"{key}={val}")
p.write_text("\n".join(out) + "\n", encoding="utf-8")
p.chmod(0o600)
PY
}

if [[ -n "${ORIGIN_CONTRACT:-}" && -n "${DESTINATION_CONTRACT:-}" ]] && \
   [[ "$(cast code "$ORIGIN_CONTRACT" --rpc-url "$ORIGIN_RPC_URL")" != "0x" ]] && \
   [[ "$(cast code "$DESTINATION_CONTRACT" --rpc-url "$DEST_RPC_URL")" != "0x" ]]; then
  echo "[1/4] Reusing already-deployed Base Sepolia contracts:"
  echo "ORIGIN_CONTRACT=$ORIGIN_CONTRACT"
  echo "DESTINATION_CONTRACT=$DESTINATION_CONTRACT"
else
  echo "[1/4] Deploying OriginRiskEmitter and DestinationLiquidatorGuard on chain $ORIGIN_CHAIN_ID..."
  forge script script/DeployOriginAndDestination.s.sol:DeployOriginAndDestination \
    --rpc-url "$ORIGIN_RPC_URL" \
    --broadcast

  echo "[2/4] Extracting deployed contract addresses from Foundry broadcast artifact..."
  eval "$(python3 - "broadcast/DeployOriginAndDestination.s.sol/${ORIGIN_CHAIN_ID}/run-latest.json" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
origin = dest = ""
for tx in data.get("transactions", []):
    if tx.get("contractName") == "OriginRiskEmitter" and tx.get("contractAddress"):
        origin = tx["contractAddress"]
    elif tx.get("contractName") == "DestinationLiquidatorGuard" and tx.get("contractAddress"):
        dest = tx["contractAddress"]
if not origin or not dest:
    raise SystemExit("Failed to parse OriginRiskEmitter / DestinationLiquidatorGuard addresses from broadcast JSON")
print(f"export ORIGIN_CONTRACT={origin}")
print(f"export DESTINATION_CONTRACT={dest}")
PY
)"
  _update_env_var ORIGIN_CONTRACT "$ORIGIN_CONTRACT"
  _update_env_var DESTINATION_CONTRACT "$DESTINATION_CONTRACT"
  echo "ORIGIN_CONTRACT=$ORIGIN_CONTRACT"
  echo "DESTINATION_CONTRACT=$DESTINATION_CONTRACT"
fi

echo "[3/4] Deploying ReactiveRiskSentinel on Reactive Lasna ($LASNA_CHAIN)..."
forge script script/DeployReactiveSentinel.s.sol:DeployReactiveSentinel \
  --rpc-url "$REACTIVE_LASNA_RPC_URL" \
  --broadcast

eval "$(python3 - "broadcast/DeployReactiveSentinel.s.sol/${LASNA_CHAIN}/run-latest.json" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
reactive = ""
for tx in data.get("transactions", []):
    if tx.get("contractName") == "ReactiveRiskSentinel" and tx.get("contractAddress"):
        reactive = tx["contractAddress"]
if not reactive:
    raise SystemExit("Failed to parse ReactiveRiskSentinel address from broadcast JSON")
print(f"export REACTIVE_CONTRACT={reactive}")
PY
)"
_update_env_var REACTIVE_CONTRACT "$REACTIVE_CONTRACT"
echo "REACTIVE_CONTRACT=$REACTIVE_CONTRACT"

echo "[4/4] Emitting risk alert and measuring full cross-chain callback latency..."
uv run python scripts/measure_loop_latency.py
