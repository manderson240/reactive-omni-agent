# Reactive Omni Buildathon: Developer Feedback Report
## What worked, what was confusing, and what I would change

**Hackathon**: [Reactive Omni Buildathon (DoraHacks)](https://dorahacks.io/hackathon/reactive-omni-buildathon/detail)  
**Project**: Reactive Omni Sentinel  
**Library used**: `reactive-lib` (git submodule in `lib/reactive-lib`), Foundry `forge 1.9.0`  
**Author**: Mike Anderson (`github.com/manderson240`), solo builder  
**Repository**: https://github.com/manderson240/reactive-omni-agent  

---

## 1. Summary

I built three contracts on `reactive-lib`: an origin contract that emits `CollateralRatioAlert`, a reactive contract (`ReactiveRiskSentinel`) that subscribes to it and emits a `Callback` when `currentRatio < minRatio`, and a destination guard (`DestinationLiquidatorGuard`) that receives the callback. A small Python package runs the same threshold check off-chain and signs a receipt.

All the testing behind this report is local, in Foundry. No deployment to Base Sepolia or Lasna is recorded in this repo, so this report covers writing and testing the contracts, not running them on the network.

---

## 2. What worked

### A. Small base contracts
- `AbstractReactive` and `AbstractCallback` are short enough to read in full. Extending them gave me `service`, `vm`, `vmOnly`, `rvmIdOnly` and the payment plumbing without any other setup.
- `service.subscribe(chainId, contract, topic0, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE)` was clear once I saw `REACTIVE_IGNORE` used as the wildcard.

### B. `LogRecord` in `react`
- Getting the whole log as one `IReactive.LogRecord` struct made decoding simple: indexed fields come from `topic_1` and `topic_2`, the rest from `abi.decode(log.data, ...)`.
- Because `react` takes a plain struct, I could build a `LogRecord` by hand in a Foundry test and call `react()` directly. That covered the decode and threshold logic, including a 256-run fuzz test over the two ratios.

### C. The callback payload convention
- Emitting `Callback(chainId, contract, gasLimit, payload)` is a simple interface. Leaving the first address argument as `address(0)` for the relayer to fill with the RVM ID worked fine with `abi.encodeWithSignature`.

---

## 3. What was confusing

### A. Testing the subscription path locally
- **Issue**: `detectVm()` decides ReactVM vs top-level Reactive Network by checking for code at `0x...fffFfF`. In a plain Foundry test there is no code there, so every contract thinks it is inside a ReactVM, and the constructor branch that calls `service.subscribe(...)` never runs.
- **Impact**: my tests never exercise the subscription. My contract also has a `setVmForTesting` setter that the tests call. Since `vm` is already `true` in Foundry, the setter is unnecessary there, and it is a hazard in a production contract because it has no access control. I need to remove it.

### B. `rvmIdOnly` does not authenticate the caller
- **Issue**: `rvmIdOnly(_rvm_id)` checks that the `_rvm_id` argument matches the stored RVM ID (or that the stored ID is zero). It does not look at `msg.sender`. Caller authentication comes from a separate modifier, `authorizedSenderOnly` in `AbstractPayer`.
- **Impact**: I used only `rvmIdOnly` on my destination functions. A throwaway Foundry test confirmed that any address can call `executeDefensiveAction` by passing the deployer address as the first argument. My own "rejects unauthorized RVM" test did not catch this, because it only changes the argument. This was my bug, but the modifier name made it easy to think one check was enough. I fixed it by adding `authorizedSenderOnly` to both callback functions, and the tests now call them from an outside address with the correct RVM ID and expect a revert.

### C. Subscription funding
- **Issue**: I could not tell from the library how much native token a reactive contract needs at deploy time for its subscription and callbacks. My deploy script sends `0.05 ether` as a guess.

---

## 4. Recommendations

1. **A local test kit.** A Foundry helper that deploys a mock system contract at `0x...fffFfF` (so the top-level subscription branch runs) and a mock relayer that forwards an emitted `Callback` to the destination with the RVM ID filled in. That would let a full origin to reactive to destination round trip run in one `forge test`.
2. **A combined callback modifier.** Something like `callbackOnly(_rvm_id)` in `AbstractCallback` that applies both `authorizedSenderOnly` and the RVM ID check, plus a note in the docs that `rvmIdOnly` alone does not check the caller.
3. **Documented funding guidance.** A short table or formula for how much to send to a reactive contract at deploy time, and how `coverDebt()` fits in.

---

## 5. Status

The contracts compile and 7 of 7 Foundry tests pass locally (7.11 ms on my machine). Before deploying I plan to add caller authentication and replay protection on the path the callback actually uses, remove `setVmForTesting`, and restrict who can call `emitRiskAlert`.
