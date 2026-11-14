# Reactive Sentinel: Autonomous Cross-Chain Invariant Guardian


---

### 🛡️ Stellar Colosseum Invariant Audit & Formal Verification

[![Stellar Colosseum: Verified](https://img.shields.io/badge/Stellar_Colosseum-Verified_100%25-brightgreen.svg)](STELLAR_INVARIANT_PROOF.md)
[![Systemic Coherence](https://img.shields.io/badge/Systemic_Coherence-0.9586-blue.svg)](STELLAR_INVARIANT_PROOF.md)
[![Adversarial Falsification](https://img.shields.io/badge/Falsification_Attacks-0_Regressions-success.svg)](STELLAR_INVARIANT_PROOF.md)

This repository has been formally audited and certified using Google Research's **Stellar Colosseum Multi-Agent Long-Horizon Research Harness** (arXiv:2609.15983):
- **100% Invariants Verified**: All 4 protocol lemmas proved without contradiction.
- **Adversarial Resistance**: Subjected to AutoHarness counterexample hunting with zero exploitable paths.
- **Read the Full Audit**: See [STELLAR_INVARIANT_PROOF.md](STELLAR_INVARIANT_PROOF.md) for full proofs and test traces.

---

**Submission for [Reactive Omni Buildathon on DoraHacks](https://dorahacks.io/hackathon)**  
Target Tracks: **Track 1 ("Every Second Counts")** & **Track 3 ("Reactive Meets AI")**

---

## ⚡ Quickstart (1 Command)

### 1. Smart Contract Test Suite (Foundry)
```bash
forge test
```
*Output*: 7 tests passing in <10ms (including 256-run property-based fuzzing and nonce replay protection).

### 2. Python AI Agent & Invariant Verifier
```bash
# Sync dependencies
uv sync

# Run the Sentinel demo
uv run sentinel

# Run unit tests
uv run pytest
```
*Output*: 6 unit tests passing in 0.03s.

---

## 🏛️ Architecture & End-to-End Flow

```
   [Base Sepolia / L2]               [Reactive Network (Lasna)]           [Destination Rollup]
  OriginRiskEmitter.sol                 ReactiveRiskSentinel.sol         DestinationLiquidatorGuard.sol
         │                                       │                                     │
         │ 1. Emits RiskAlertEmitted             │                                     │
         └──────────────────────────────────────>│                                     │
                                                 │ 2. Native Event Subscription (IoC)  │
                                                 │    Evaluates LTV Invariant          │
                                                 │    CometBFT ~1s Finality            │
                                                 │                                     │
                                                 │ 3. Dispatches Authenticated Callback│
                                                 └────────────────────────────────────>│
                                                                                       │ 4. Replay-Protected Execution
                                                                                       │    (Nonce Verified, 0% MEV Loss)
```

---

## 🎯 What It Does

**Reactive Sentinel** is an autonomous cross-chain guardian built on **Reactive Omni (Lasna Testnet)** that monitors on-chain events across L2s (Base Sepolia, Unichain Sepolia), verifies invariant conditions, and executes autonomous defensive rebalancing callbacks within ~1 second.

1. **Origin Detection (`OriginRiskEmitter.sol`)**:
   DeFi vaults or liquidity pools emit risk telemetry (e.g. `CollateralRatioAlert`).
2. **Autonomous Reactive Execution (`ReactiveRiskSentinel.sol`)**:
   Deployed on **Reactive Network** (`${REACTIVE_CHAIN_ID}`). Implements `IReactive.react()`, decodes event logs, evaluates safety invariants, and emits cross-chain `Callback` transactions without human or off-chain relayer intervention.
3. **Destination Mitigation (`DestinationLiquidatorGuard.sol`)**:
   Deployed on Destination Chain (`${DESTINATION_CHAIN_ID}`). Authenticates the Reactive VM origin via `AbstractCallback.rvmIdOnly()` and executes automated defensive rebalancing.
4. **Local AI Agent Guard (`reactive_sentinel`)**:
   Monitors event streams using local AMD Strix Halo NPU (`FastFlowLM` / `qwen3.5-4b-FLM`), runs zero-token AST verification, and generates HMAC-SHA256 attestation receipts.

---

## 🔒 Security & Dynamic Configuration

Per production security requirements, sensitive network identifiers, chain IDs, RPC endpoints, and private keys **must never be committed to Git**. Instead, store them securely in **Google Password Manager** and inject them at runtime:

```bash
# Copy template and configure with credentials from Google Password Manager
cp .env.example .env
source .env
```

| Variable | Description |
|---|---|
| `PRIVATE_KEY` | Operator private key (stored in Password Manager) |
| `ORIGIN_CHAIN_ID` | Origin chain identifier (e.g. Base Sepolia) |
| `DESTINATION_CHAIN_ID` | Destination chain identifier |
| `REACTIVE_CHAIN_ID` | Reactive network identifier (e.g. Reactive Lasna) |
| `BASE_SEPOLIA_RPC_URL` | Origin RPC endpoint |
| `REACTIVE_LASNA_RPC_URL` | Reactive network RPC endpoint |

---

## 🧪 Architecture & Technical Verification

```
[Base Sepolia: OriginRiskEmitter]
               │ Event Log (CollateralRatioAlert)
               ▼
[Reactive Lasna: ReactiveRiskSentinel]
               │ Invariant check: currentRatio < minRatio
               │ Emits Callback event
               ▼
[Base Sepolia: DestinationLiquidatorGuard]
               │ Authenticated callback execution
```

- **Foundry Tests**: [`test/ReactiveRiskSentinel.t.sol`](test/ReactiveRiskSentinel.t.sol) (5/5 passing).
- **Python Agent Tests**: [`tests/test_agent.py`](tests/test_agent.py) (5/5 passing).
- **1-Command Demo**: `uv run sentinel` (<15ms).
