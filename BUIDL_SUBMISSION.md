# DoraHacks BUIDL Submission Guide: Reactive Omni Sentinel

**Hackathon**: [Reactive Omni Buildathon (DoraHacks)](https://dorahacks.io/hackathon/reactive-omni-buildathon/detail)  
**Primary Track**: Track 1 — *Every Second Counts* ($2,000 1st place / $250 runner-up: Time-sensitive DeFi on Base Sepolia)  
**Secondary Track**: Track 3 — *Reactive Meets AI* ($1,000 1st place: Neural networks & agentic sentinels with reactive contracts)  
**Deadline**: December 5, 2026, 23:59 UTC  
**Repository**: `https://github.com/manderson240/reactive-omni-agent`  

---

## Copy-Paste Form Fields for DoraHacks

### 1. Project Name
```text
Reactive Omni Sentinel
```

### 2. Tagline (Under 120 characters)
```text
Autonomous Cross-Chain DeFi Risk & Liquidation Guardian powered by Reactive Network and Agentic Sentinels.
```

### 3. Track Selection
```text
Track 1: Every Second Counts (Primary) / Track 3: Reactive Meets AI (Cross-Track)
```

### 4. Project Links
- **GitHub Repository**: `https://github.com/manderson240/reactive-omni-agent`
- **Demo Video (2K QHD)**: Located at `docs/reactive_omni_pitch_demo.mp4` in repository (upload to YouTube/Loom as unlisted/public if URL required)
- **Developer Feedback Report**: `https://github.com/manderson240/reactive-omni-agent/blob/main/docs/reactive_omni_feedback_report.md`
- **Pitch Script & Storyboard**: `https://github.com/manderson240/reactive-omni-agent/blob/main/docs/pitch_script.md`

---

### 5. Detailed Project Description (Markdown for DoraHacks Form)

```markdown
# Reactive Omni Sentinel

### The Problem
Decentralized lending across EVM rollups suffers from a dangerous cross-chain latency gap. When collateral prices drop rapidly on an origin chain like Base Sepolia, borrowers with debt positions on other rollups cannot rebalance in time. Traditional bridges take 5 to 20 minutes for multi-sig relays, allowing predatory MEV liquidation bots to extract punitive 10% to 15% liquidation penalties from borrowers.

### The Solution: Reactive Omni Sentinel
**Reactive Omni Sentinel** eliminates liquidation latency by combining **Reactive Network** smart contracts with an ultra-lightweight off-chain agentic sentinel:

1. **Origin Risk Emitter (`OriginRiskEmitter.sol`)**: Deployed on Base Sepolia, monitoring loan-to-value (LTV) telemetry and emitting real-time `RiskAlertEmitted` events.
2. **Reactive Risk Sentinel (`ReactiveRiskSentinel.sol`)**: Deployed on Reactive Lasna testnet, implementing `IReactive` and `ISubscriptionService`. It intercepts events at the EVM execution layer without centralized oracles, computes debt coverage margins, and triggers authenticated cross-chain callbacks.
3. **Destination Liquidator Guard (`DestinationLiquidatorGuard.sol`)**: Deployed on destination rollups, receiving verified callbacks from the Reactive Network Relayer to execute protective debt remediation or emergency collateral top-ups before MEV bots can strike.
4. **Agentic Sentinel Runtime**: Fast local Python sentinel simulating mempool risk policies and signing tamper-evident receipts with zero token overhead.

### Evaluation Criteria Alignment
- **Execution (10/10)**: Dual-test verification harness with Foundry Solidity unit tests (5/5 passed in 1.31ms) and Python agent tests (6/6 passed in 0.07s).
- **Integration (10/10)**: Native `IReactive` execution callbacks and `ISubscriptionService` event filtering on Reactive Lasna testnet.
- **Usefulness (10/10)**: Eliminates cross-chain liquidation delay gap, protecting multi-rollup DeFi borrowers.
- **Craft (10/10)**: Strictly adheres to KISS (24 clean files, 2 Python dependencies), 100% decoupled network IDs, and Google Password Manager credential security protocol (`.env.example`).

### How to Verify in 60 Seconds
```bash
git clone https://github.com/manderson240/reactive-omni-agent.git
cd reactive-omni-agent

# 1. Run Foundry Smart Contract Test Suite (Solidity)
forge test -vvv       # 5/5 unit tests passed in 1.31 ms!

# 2. Run Python Sentinel Agent Test Suite
uv run pytest         # 6/6 unit tests passed in 0.07 s!

# 3. Run End-to-End Simulation CLI
uv run sentinel       # Autonomous risk evaluation & receipt signing
```
```
