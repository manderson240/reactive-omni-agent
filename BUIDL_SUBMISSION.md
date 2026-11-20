# DoraHacks BUIDL Submission: Reactive Omni Sentinel

**Hackathon**: [Reactive Omni Buildathon (DoraHacks)](https://dorahacks.io/hackathon/reactive-omni-buildathon/detail)  
**Primary Track**: Track 1: *Every Second Counts* ($2,000 1st place / $250 runner-up: Time-sensitive DeFi on Base Sepolia)  
**Secondary Track**: Track 3: *Reactive Meets AI* ($1,000 1st place: Neural networks & agentic sentinels with reactive contracts)  
**Deadline**: December 5, 2026, 23:59 UTC  
**Repository**: https://github.com/manderson240/reactive-omni-agent  

This file mirrors what I enter in the DoraHacks form.

---

## Form fields

### Name
```text
Reactive Omni Sentinel
```

### Brief description (120 characters max; this one is 119)
```text
Reactive contract that turns an origin-chain collateral alert into a destination-chain callback, plus a Python checker.
```

### Tags
```text
DeFi, Reactive Network, Cross-chain
```

### Team
```text
Mike Anderson (Solo builder, github.com/manderson240)
```

### Links
- GitHub: https://github.com/manderson240/reactive-omni-agent
- Demo video: https://github.com/manderson240/reactive-omni-agent/raw/main/docs/reactive_omni_pitch_demo.mp4
- Feedback report: https://github.com/manderson240/reactive-omni-agent/blob/main/docs/reactive_omni_feedback_report.md

### Contact
- Telegram: `manderson240`
- Discord: `miked238725`

---

## Description

# Reactive Omni Sentinel

### Why I built this
A lending position can sit on one chain while the price move that endangers it happens on another. I wanted to see how far Reactive Network's event subscriptions get you toward reacting to that on-chain, without running my own off-chain poller: an alert on the origin chain should lead straight to a call on the destination chain.

### How it works
I wrote three contracts and a small Python package.

1. `OriginRiskEmitter.emitRiskAlert` emits `CollateralRatioAlert(vaultId, owner, currentRatio, minRatio, recommendedAction)`. It is a stand-in for a lending vault so I can raise test alerts.
2. `ReactiveRiskSentinel` extends `AbstractReactive`. Its constructor subscribes to `CollateralRatioAlert` on the origin contract. `react(LogRecord)` decodes the log and, when `currentRatio < minRatio`, emits a Reactive `Callback` that calls `executeDefensiveAction` on the destination guard with a 250000 gas limit.
3. `DestinationLiquidatorGuard` extends `AbstractCallback`. `executeDefensiveAction` (guarded by `authorizedSenderOnly` and `rvmIdOnly`) records the action and emits `RebalanceExecuted`. A second function, `executeDefensiveActionWithNonce`, also blocks replays of the same nonce.
4. The Python package (`src/reactive_sentinel/`) runs the same threshold rule off-chain in `verify_risk_event`, rejects action codes outside {1, 2, 3}, and signs an HMAC-SHA256 receipt per event. The `sentinel` CLI runs it on two hardcoded events.

### Reactive Network building blocks I used
- `AbstractReactive`, `service.subscribe(...)` and `REACTIVE_IGNORE` for topic filtering.
- `react(LogRecord)` with the `vmOnly` modifier.
- The `Callback` event with the first address slot left as `address(0)` for the RVM ID.
- `AbstractCallback`, `authorizedSenderOnly` and `rvmIdOnly` on the destination side.

What I learned about these is in the feedback report: `docs/reactive_omni_feedback_report.md`.

### Track 3 (Reactive Meets AI)
The off-chain part is a deterministic checker and signer that an agent could call before trusting a callback. I did not connect an LLM or any model to it, and the Python package does not read chain events yet. I am entering Track 3 on the strength of that design, not a working AI integration.

### Limits
- No deployment is recorded in this repo. The Foundry tests call `react()` directly; they do not go through a live subscription or relayer.
- My first version of `executeDefensiveAction` checked only the `_rvmId` argument, not `msg.sender`, so any address could call it. I fixed it by adding `authorizedSenderOnly`, with tests that call from an outside address.
- The reactive payload calls the function without replay protection. `setVmForTesting` and `emitRiskAlert` have no access control.
- No funds move; the guard only counts actions and emits an event.

### Verification
On my machine, 7 of 7 Foundry tests pass in 7.11 ms (one of them is a 256-run fuzz test) and 6 of 6 Python tests pass in 0.03 s. The demo CLI finishes in 0.08 ms.

```bash
git clone --recurse-submodules https://github.com/manderson240/reactive-omni-agent.git
cd reactive-omni-agent
forge test
uv sync --extra dev
uv run pytest
uv run sentinel
```

---

## Architecture diagrams

See [README.md](README.md#how-it-works) for the flowchart and sequence diagram.
