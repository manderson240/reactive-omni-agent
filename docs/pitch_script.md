# Reactive Omni Agent: Video Pitch Script & Storyboard

**Competition**: Reactive Omni Buildathon (DoraHacks)  
**Title**: Reactive Sentinel: Autonomous Cross-Chain Risk & Liquidation Guardian  
**Target Video Duration**: 2 minutes 30 seconds  
**Target Resolution**: 2560x1440 (2K QHD)  

---

## Scene Breakdown

### Scene 1: Hero Opening & Title Card (0:00 - 0:25)
- **Visual**: Dark high-contrast title card with cyan/emerald badges, showcasing the Reactive Network logo, repository statistics (24 files, KISS Grade A+), and key capabilities:
  - Sub-millisecond local policy execution
  - Native Reactive Network event-driven callbacks (`IReactive`, `ISubscriptionService`)
  - 100% test pass rate (Solidity Foundry + Python Sentinel)
  - Zero hardcoded keys or chain IDs
- **Narration**:
  > "Welcome to Reactive Sentinel, an autonomous cross-chain risk and liquidation guardian built for the Reactive Omni Buildathon on DoraHacks. By combining Reactive Network's event-driven smart contract architecture with an ultra-lightweight agentic sentinel, Reactive Sentinel eliminates DeFi liquidation latency and protects borrowers across EVM rollups."

---

### Scene 2: The Cross-Chain DeFi Liquidation Bottleneck (0:25 - 0:55)
- **Visual**: Diagram showing the fragmented DeFi lending landscape across Base, Arbitrum, and Ethereum mainnet. Highlight the vulnerability: when market volatility drops health factors on an origin chain, cross-chain bridge delays prevent collateral rebalancing before predatory MEV bots liquidate the position.
- **Narration**:
  > "Decentralized lending across EVM chains faces a fundamental challenge: cross-chain latency. When collateral prices shift rapidly on an origin chain like Base Sepolia, users with positions spread across other rollups are vulnerable. Traditional bridges take minutes to relay messages, allowing predatory liquidation searchers to extract steep 10 to 15 percent penalties. DeFi needs autonomous, event-driven execution that reacts the instant risk thresholds are breached."

---

### Scene 3: Reactive Network Smart Contract Architecture (0:55 - 1:30)
- **Visual**: Technical architecture diagram highlighting the three-tier smart contract system:
  1. `OriginRiskEmitter.sol`: Deployed on Base Sepolia, emitting high-priority `RiskAlertEmitted` events.
  2. `ReactiveRiskSentinel.sol`: Deployed on Reactive Lasna testnet, implementing `IReactive` to autonomously intercept events and dispatch callbacks.
  3. `DestinationLiquidatorGuard.sol`: Deployed on destination rollup, executing authorized debt rebalancing.
- **Narration**:
  > "Reactive Sentinel solves this with a three-tier smart contract architecture powered by Reactive Network. On the origin chain, the Origin Risk Emitter monitors vault ratios and emits real-time risk alerts. On the Reactive Network Lasna testnet, our Reactive Risk Sentinel subscribes to these events at the EVM execution layer. Without relying on centralized oracles, it evaluates debt coverage margins and triggers an authenticated callback to the Destination Liquidator Guard, executing protective debt remediation before liquidation bots can strike."

---

### Scene 4: Dual Verification Suite: Foundry & Python Agent (1:30 - 2:00)
- **Visual**: Split terminal view showing:
  - Left: `forge test -vvv` passing 5/5 Solidity tests in 1.3 milliseconds.
  - Right: `uv run pytest` passing 6/6 agent tests in 0.07 seconds, followed by `uv run sentinel` executing the end-to-end simulation.
- **Narration**:
  > "Security and reliability are paramount. Reactive Sentinel features a complete dual verification harness. In Solidity, our Foundry test suite verifies event subscriptions, access control, and cross-chain payload encoding in just 1.3 milliseconds. In Python, our lightweight Sentinel agent simulates mempool risk policies and generates tamper-evident receipts with zero LLM token overhead, ensuring predictable, deterministic execution."

---

### Scene 5: Production Security & KISS Architecture (2:00 - 2:30)
- **Visual**: Summary card showcasing:
  - Zero hardcoded secrets, RPC endpoints, or chain IDs
  - Environment variable injection via Google Password Manager
  - Clean repository: 24 files, 2 Python dependencies, zero bloated frameworks
  - GitHub repository link: `github.com/manderson240/reactive-omni-agent`
- **Narration**:
  > "Reactive Sentinel adheres strictly to KISS engineering principles: a clean 24-file codebase with zero vendor bloat. All network IDs and sensitive credentials are fully decoupled and managed securely through Google Password Manager environment injection. Reactive Sentinel represents the future of autonomous, event-driven cross-chain DeFi. Thank you, and explore the code on GitHub."
