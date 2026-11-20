#!/usr/bin/env python3
"""Automated 2560x1440 (2K QHD) 6-Scene Code Walkthrough & Pitch Video Generator
for Reactive Omni Sentinel (DoraHacks Reactive Omni Buildathon).
"""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image


WIDTH = 2560
HEIGHT = 1440
CHROME_CAPTURE_HEIGHT = 1527
REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_slice(rel_path: str, start_line: int, end_line: int) -> str:
    """Load exact verbatim source lines (zero ellipses) and HTML-escape safely."""
    lines = (REPO_ROOT / rel_path).read_text(encoding="utf-8").splitlines()
    return html.escape("\n".join(lines[start_line - 1 : end_line]))


REACTIVE_CONTRACT_PART1 = _load_slice("src/ReactiveRiskSentinel.sol", 7, 50)
REACTIVE_CONTRACT_PART2 = _load_slice("src/ReactiveRiskSentinel.sol", 50, 91)
VERIFIER_PY_CODE = _load_slice("src/reactive_sentinel/verifier.py", 13, 83)
AGENT_PY_CODE = _load_slice("src/reactive_sentinel/agent.py", 16, 67)

SCENES = [
    {
        "id": "scene0_title_hero",
        "narration": (
            "Reactive Omni Sentinel. I built this for the DoraHacks Reactive Omni Buildathon, tracks one and three. "
            "An origin contract emits a collateral ratio alert. "
            "A reactive contract on Reactive Network subscribes to it and, when the ratio is under its threshold, "
            "emits a callback to a guard contract on the destination chain. "
            "A small Python package runs the same check off chain and signs a receipt. "
            "Everything shown here runs locally: seven Foundry tests and six Python tests pass on my machine."
        ),
        "html_body": """
            <div class="header" style="text-align:center;margin-top:12px;margin-bottom:24px;">
                <span class="badge" style="font-size:20px;padding:8px 26px;">Reactive Omni Buildathon: Track 1 &amp; Track 3</span>
                <h1 style="font-size:64px;margin-top:14px;margin-bottom:10px;letter-spacing:-2px;">Reactive Omni Sentinel</h1>
                <p class="subtitle" style="font-size:26px;margin:0 auto;max-width:1950px;color:#38bdf8;font-weight:500;">
                    Origin alert to Reactive callback to destination guard, plus a Python threshold checker
                </p>
            </div>
            <div class="grid-4" style="margin-top:20px;margin-bottom:20px;">
                <div class="card" style="text-align:center;border-color:rgba(56,189,248,0.4);background:rgba(56,189,248,0.08);">
                    <h3 style="font-size:30px;color:#38bdf8;">OriginRiskEmitter</h3>
                    <p style="font-size:18px;color:#cbd5e1;">emitRiskAlert() emits CollateralRatioAlert</p>
                </div>
                <div class="card" style="text-align:center;border-color:rgba(34,197,94,0.4);background:rgba(34,197,94,0.08);">
                    <h3 style="font-size:30px;color:#22c55e;">ReactiveRiskSentinel</h3>
                    <p style="font-size:18px;color:#cbd5e1;">react(LogRecord): currentRatio &lt; minRatio emits Callback</p>
                </div>
                <div class="card" style="text-align:center;border-color:rgba(192,132,252,0.4);background:rgba(192,132,252,0.08);">
                    <h3 style="font-size:30px;color:#c084fc;">DestinationLiquidatorGuard</h3>
                    <p style="font-size:18px;color:#cbd5e1;">executeDefensiveAction() counts the action, emits RebalanceExecuted</p>
                </div>
                <div class="card" style="text-align:center;border-color:rgba(245,158,11,0.4);background:rgba(245,158,11,0.08);">
                    <h3 style="font-size:30px;color:#f59e0b;">Tests</h3>
                    <p style="font-size:18px;color:#cbd5e1;">Foundry 7/7 (one 256-run fuzz test), pytest 6/6</p>
                </div>
            </div>
            <div class="flow-container" style="margin-top:16px;">
                <div class="chip chip-blue" style="font-size:17px;padding:10px 20px;">Origin chain</div>
                <div class="chip chip-green" style="font-size:17px;padding:10px 20px;">Reactive Network (ReactVM)</div>
                <div class="chip chip-blue" style="font-size:17px;padding:10px 20px;">Destination chain</div>
                <div class="chip chip-green" style="font-size:17px;padding:10px 20px;">Local tests only, not deployed yet</div>
            </div>
        """,
    },
    {
        "id": "scene1_problem_workflow",
        "narration": (
            "The idea: a lending position can sit on one chain while the price move that endangers it happens on another. "
            "Step one: OriginRiskEmitter emits CollateralRatioAlert. "
            "Step two: ReactiveRiskSentinel receives the log as a LogRecord inside the ReactVM, checks topic zero, "
            "decodes the ratios, and emits a Callback when the current ratio is below the minimum. "
            "Step three: DestinationLiquidatorGuard receives the call. "
            "It records the action and emits an event; it does not move any funds."
        ),
        "html_body": """
            <div class="header">
                <span class="badge">Architecture</span>
                <h1>Event-driven callbacks on Reactive Network</h1>
                <p class="subtitle">Origin alert, ReactVM check, destination guard.</p>
            </div>
            <div class="flow-container" style="margin-top:24px;">
                <div class="flow-step">
                    <div class="flow-num">01</div>
                    <h4>Origin alert</h4>
                    <p>OriginRiskEmitter emits indexed vaultId and owner, with ratios and action code in data.</p>
                    <div class="chip">CollateralRatioAlert</div>
                </div>
                <div class="flow-arrow">&rarr;</div>
                <div class="flow-step highlight">
                    <div class="flow-num">02</div>
                    <h4>ReactiveRiskSentinel</h4>
                    <p>react(LogRecord) checks currentRatio &lt; minRatio and emits Callback.</p>
                    <div class="chip chip-blue">250000 gas limit</div>
                </div>
                <div class="flow-arrow">&rarr;</div>
                <div class="flow-step">
                    <div class="flow-num">03</div>
                    <h4>Destination guard</h4>
                    <p>DestinationLiquidatorGuard runs rvmIdOnly, increments totalRebalances, emits RebalanceExecuted.</p>
                    <div class="chip chip-green">No funds move</div>
                </div>
            </div>
            <div class="grid-2" style="margin-top:24px;">
                <div class="card success">
                    <h3>What it does</h3>
                    <ul>
                        <li><strong>Subscription:</strong> constructor calls service.subscribe for CollateralRatioAlert</li>
                        <li><strong>Check:</strong> react() emits a Callback only when currentRatio &lt; minRatio</li>
                        <li><strong>Python:</strong> verify_risk_event checks the same rule and action_code in {1,2,3}</li>
                        <li><strong>Receipt:</strong> HMAC-SHA256 over event, chain IDs, outcome and timestamp</li>
                    </ul>
                </div>
                <div class="card danger">
                    <h3>What it does not do yet</h3>
                    <ul>
                        <li><strong>Deployment:</strong> none recorded in the repo</li>
                        <li><strong>Caller check:</strong> the guard checks the rvmId argument, not msg.sender</li>
                        <li><strong>Replay guard:</strong> only on executeDefensiveActionWithNonce, not the callback path</li>
                        <li><strong>Chain link:</strong> the Python package does not read events or send transactions</li>
                    </ul>
                </div>
            </div>
        """,
    },
    {
        "id": "scene2_core_source_code",
        "narration": (
            "Here is the Solidity contract in src/ReactiveRiskSentinel.sol, lines seven through ninety-one. "
            "On the left, the constructor subscribes to CollateralRatioAlert on the origin chain and contract. "
            "On the right, the vmOnly react function reads vaultId and owner from the indexed topics, "
            "decodes the ratios, and emits the destination Callback when the current ratio is below the minimum. "
            "The first address slot is left as zero for the relayer to fill with the RVM ID."
        ),
        "html_body": f"""
            <div class="header">
                <span class="badge">Code: Reactive Network contract</span>
                <h1>ReactiveRiskSentinel.sol</h1>
                <p class="subtitle">From <code>src/ReactiveRiskSentinel.sol</code>, lines 7 to 91.</p>
            </div>
            <div class="code-grid-2">
                <div class="code-box">
                    <div class="linux-bar">
                        <span class="linux-tab">src/ReactiveRiskSentinel.sol (Lines 7 to 50)</span>
                        <div class="linux-controls"><span>_</span><span>&#9633;</span><span>x</span></div>
                    </div>
                    <pre style="font-size:14.2px;line-height:1.30;">{REACTIVE_CONTRACT_PART1}</pre>
                    <div class="eval-flow">
                        <span class="flow-pill pass">service.subscribe()</span>
                        <span class="flow-pill pass">ALERT_TOPIC_0</span>
                    </div>
                </div>
                <div class="code-box">
                    <div class="linux-bar">
                        <span class="linux-tab">src/ReactiveRiskSentinel.sol (Lines 50 to 91)</span>
                        <div class="linux-controls"><span>_</span><span>&#9633;</span><span>x</span></div>
                    </div>
                    <pre style="font-size:14.2px;line-height:1.30;">{REACTIVE_CONTRACT_PART2}</pre>
                    <div class="eval-flow">
                        <span class="flow-pill pass">vmOnly</span>
                        <span class="flow-pill pass">emit Callback</span>
                    </div>
                </div>
            </div>
        """,
    },
    {
        "id": "scene3_verifier_source_code",
        "narration": (
            "Next is the Python side. "
            "On the left, src/reactive_sentinel/verifier.py lines thirteen through eighty-three rejects non-positive IDs and ratios "
            "and any action code other than one, two, or three, then applies the same ratio rule as the contract. "
            "On the right, ReactiveSentinelAgent reads chain IDs from the environment and signs a ReactiveAttestationReceipt for each event. "
            "There is no model call in this package."
        ),
        "html_body": f"""
            <div class="header">
                <span class="badge">Code: off-chain checker</span>
                <h1>verifier.py and agent.py</h1>
                <p class="subtitle">The Python threshold check and receipt signer.</p>
            </div>
            <div class="code-grid-2">
                <div class="code-box">
                    <div class="linux-bar">
                        <span class="linux-tab">src/reactive_sentinel/verifier.py (Lines 13 to 83)</span>
                        <div class="linux-controls"><span>_</span><span>&#9633;</span><span>x</span></div>
                    </div>
                    <pre style="font-size:13.0px;line-height:1.23;">{VERIFIER_PY_CODE}</pre>
                    <div class="eval-flow">
                        <span class="flow-pill pass">VALID_ACTION_CODES</span>
                        <span class="flow-pill pass">current_ratio &lt; min_ratio</span>
                    </div>
                </div>
                <div class="code-box">
                    <div class="linux-bar">
                        <span class="linux-tab">src/reactive_sentinel/agent.py (Lines 16 to 67)</span>
                        <div class="linux-controls"><span>_</span><span>&#9633;</span><span>x</span></div>
                    </div>
                    <pre style="font-size:13.8px;line-height:1.27;">{AGENT_PY_CODE}</pre>
                    <div class="eval-flow">
                        <span class="flow-pill pass">Chain IDs from env</span>
                        <span class="flow-pill pass">HMAC receipt</span>
                    </div>
                </div>
            </div>
        """,
    },
    {
        "id": "scene4_honest_vs_adversarial_exec",
        "narration": (
            "On the left is the demo CLI. Vault one oh one is at one hundred ten percent against a one hundred twenty-five percent minimum, "
            "so a callback is required; vault one oh two is healthy, so none is. "
            "The Lasna status lines in this output are fixed strings: the demo does not connect to any network. "
            "On the right are the Foundry tests for the destination guard. "
            "A wrong RVM ID argument reverts, and a repeated nonce reverts on the nonce variant."
        ),
        "html_body": """
            <div class="header">
                <span class="badge">Runs from my machine</span>
                <h1>Demo CLI and destination guard tests</h1>
                <p class="subtitle">Output trimmed to the relevant lines.</p>
            </div>
            <div class="code-grid-2">
                <div class="terminal-mini">
                    <div class="linux-bar">
                        <span class="linux-tab">uv run sentinel</span>
                        <div class="linux-controls"><span>_</span><span>&#9633;</span><span>x</span></div>
                    </div>
                    <div class="term-lines" style="font-size:17px;">
                        <p class="t-line"><span class="t-prompt">$</span> uv run sentinel</p>
                        <p class="t-line t-cyan">[2] Ingesting Risk Event: 'evt-vault-101-margin-call'</p>
                        <p class="t-line t-indent">Vault ID: 101 | Collateral Ratio: 110% | Min Ratio: 125%</p>
                        <p class="t-line t-indent">[OK] Action Triggered:  CALLBACK REQUIRED -&gt; executeDefensiveAction(vault=101, action=1)</p>
                        <p class="t-line t-cyan">[3] Ingesting Normal Event: 'evt-vault-102-healthy'</p>
                        <p class="t-line t-indent">Vault ID: 102 | Collateral Ratio: 155% | Min Ratio: 125%</p>
                        <p class="t-line t-indent">[OK] Action Triggered:  NO CALLBACK (compute and gas conserved)</p>
                        <p class="t-line t-yellow">Lasna status lines are fixed strings; no network is contacted.</p>
                    </div>
                </div>
                <div class="terminal-mini danger-border">
                    <div class="linux-bar danger-header">
                        <span class="linux-tab-danger">forge test</span>
                        <div class="linux-controls"><span>_</span><span>&#9633;</span><span>x</span></div>
                    </div>
                    <div class="term-lines" style="font-size:17px;">
                        <p class="t-line"><span class="t-prompt">$</span> forge test</p>
                        <p class="t-line"><span class="t-green">[PASS]</span> test_destination_guard_executes_callback_from_authorized_rvm()</p>
                        <p class="t-line"><span class="t-green">[PASS]</span> test_destination_guard_rejects_unauthorized_rvm()</p>
                        <p class="t-line"><span class="t-green">[PASS]</span> test_destination_guard_replay_protection_blocks_duplicate_nonce()</p>
                        <p class="t-line t-yellow">Known gap: the guard checks the rvmId argument, not msg.sender.</p>
                        <p class="t-line t-yellow">A random caller passing the deployer address is accepted.</p>
                    </div>
                </div>
            </div>
        """,
    },
    {
        "id": "scene5_verification_and_impact",
        "narration": (
            "To check it yourself: forge test runs seven Foundry tests, one of them a fuzz test with two hundred fifty-six runs; "
            "on my machine the suite finished in about seven milliseconds. "
            "uv run pytest runs six Python tests. "
            "Before deploying I still need caller authentication and replay protection on the callback path, "
            "and to remove the test-only setter. The code is on GitHub at manderson240 slash reactive-omni-agent."
        ),
        "html_body": """
            <div class="header">
                <span class="badge">Verification</span>
                <h1>Foundry 7/7 and pytest 6/6</h1>
                <p class="subtitle">Local runs. Timings are from my machine.</p>
            </div>
            <div class="grid-2" style="margin-top:18px;gap:26px;">
                <div class="terminal-window" style="height:640px;">
                    <div class="linux-bar">
                        <span class="linux-tab">forge test &amp;&amp; uv run pytest -q</span>
                        <div class="linux-controls"><span>_</span><span>&#9633;</span><span>x</span></div>
                    </div>
                    <div class="terminal-content" style="font-size:14.2px;line-height:1.42;">
                        <p class="cmd">$ forge test</p>
                        <p><span class="pass">[PASS]</span> test_react_triggers_callback_when_ratio_under_threshold()</p>
                        <p><span class="pass">[PASS]</span> test_react_ignores_safe_ratio()</p>
                        <p><span class="pass">[PASS]</span> test_react_ignores_unrelated_event_topics()</p>
                        <p><span class="pass">[PASS]</span> test_fuzz_risk_ratio_evaluation(uint256,uint256) (runs: 256)</p>
                        <p>Suite result: ok. 7 passed; 0 failed; 0 skipped; finished in 7.11ms</p>
                        <p class="cmd" style="margin-top:8px;">$ uv run pytest -q</p>
                        <p>6 passed in 0.03s</p>
                    </div>
                </div>
                <div class="card" style="display:flex;flex-direction:column;justify-content:space-between;height:640px;">
                    <div>
                        <h3 style="color:#38bdf8;">Before deployment</h3>
                        <ul>
                            <li><strong>Guard:</strong> add authorizedSenderOnly to executeDefensiveAction</li>
                            <li><strong>Replay:</strong> send a nonce on the callback path</li>
                            <li><strong>Test setter:</strong> remove setVmForTesting</li>
                            <li><strong>Alerts:</strong> restrict who can call emitRiskAlert</li>
                            <li><strong>Repository:</strong> <code>manderson240/reactive-omni-agent</code></li>
                        </ul>
                    </div>
                    <div class="card success" style="padding:18px;">
                        <h4 style="color:#22c55e;font-size:20px;margin-bottom:6px;">Run it locally</h4>
                        <div class="code-pill" style="font-size:15.5px;">forge test &amp;&amp; uv run pytest -q</div>
                    </div>
                </div>
            </div>
        """,
    },
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" style="background-color:#030712;width:100%;height:100%;margin:0;padding:0;">
<head><meta charset="UTF-8"><style>
* { box-sizing:border-box; margin:0; padding:0; }
html, body {
  width:2560px; height:1440px;
  background:radial-gradient(circle at 50% 12%, #182234 0%, #0b0f19 55%, #030712 100%) !important;
  font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color:#f8fafc; padding:30px 60px;
  display:flex; flex-direction:column; justify-content:space-between; overflow:hidden;
}
.header { margin-bottom:12px; }
.badge { display:inline-block; padding:6px 18px; background:rgba(56,189,248,0.15); border:1px solid rgba(56,189,248,0.4); border-radius:9999px; color:#38bdf8; font-size:17px; font-weight:700; text-transform:uppercase; letter-spacing:2px; margin-bottom:6px; }
h1 { font-size:46px; font-weight:800; color:#ffffff; margin-bottom:6px; letter-spacing:-1px; }
.subtitle { font-size:22px; color:#94a3b8; line-height:1.35; }
.grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:30px; }
.grid-4 { display:grid; grid-template-columns:repeat(4,1fr); gap:24px; }
.flow-container { display:flex; align-items:center; justify-content:space-between; background:rgba(30,41,59,0.45); border:1px solid rgba(148,163,184,0.2); border-radius:18px; padding:18px 32px; gap:16px; }
.flow-step { flex:1; background:#0d1322; border:1px solid #334155; border-radius:14px; padding:18px; text-align:center; }
.flow-step.highlight { border-color:#38bdf8; background:rgba(56,189,248,0.12); }
.flow-num { font-size:20px; font-weight:900; color:#38bdf8; margin-bottom:4px; }
.flow-step h4 { font-size:22px; color:#f8fafc; margin-bottom:4px; }
.flow-step p { font-size:16px; color:#94a3b8; margin-bottom:8px; line-height:1.35; }
.flow-arrow { font-size:30px; color:#64748b; padding:0 12px; font-weight:bold; }
.chip { display:inline-block; padding:6px 14px; background:#1e293b; border-radius:8px; font-size:14px; font-weight:600; color:#cbd5e1; }
.chip-blue { background:rgba(56,189,248,0.2); color:#38bdf8; border:1px solid rgba(56,189,248,0.4); }
.chip-green { background:rgba(34,197,94,0.2); color:#22c55e; border:1px solid rgba(34,197,94,0.4); }
.card { background:rgba(30,41,59,0.65); border:1px solid rgba(148,163,184,0.2); border-radius:18px; padding:24px; }
.card.danger { background:rgba(239,68,68,0.08); border-color:rgba(239,68,68,0.35); }
.card.success { background:rgba(34,197,94,0.08); border-color:rgba(34,197,94,0.35); }
.card-icon { font-size:36px; margin-bottom:8px; }
.card h3 { font-size:26px; color:#f1f5f9; margin-bottom:10px; font-weight:700; }
.card p { font-size:18px; color:#cbd5e1; line-height:1.4; }
.card ul { list-style:none; }
.card ul li { font-size:18px; color:#cbd5e1; line-height:1.8; }
.card ul li strong { color:#ffffff; }
.code-grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:26px; height:980px; }
.code-box { background:#0a0e17; border:1px solid #1e293b; border-radius:14px; overflow:hidden; display:flex; flex-direction:column; box-shadow:0 25px 50px -12px rgba(0,0,0,0.7); }
.linux-bar { background:#181f30; padding:10px 18px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #222d42; }
.linux-tab { background:#0a0e17; padding:4px 12px; border-radius:6px 6px 0 0; border:1px solid #222d42; border-bottom:none; color:#38bdf8; font-family:monospace; font-size:16px; font-weight:600; }
.linux-tab-danger { background:#0a0e17; padding:4px 12px; border-radius:6px 6px 0 0; border:1px solid rgba(239,68,68,0.4); border-bottom:none; color:#ef4444; font-family:monospace; font-size:16px; font-weight:600; }
.danger-header { background:#241319; border-bottom-color:rgba(239,68,68,0.3); }
.danger-border { border-color:rgba(239,68,68,0.45) !important; }
.linux-controls { display:flex; gap:14px; font-size:16px; color:#94a3b8; font-family:monospace; font-weight:bold; }
pre { padding:16px 22px; font-family:"JetBrains Mono","DejaVu Sans Mono",monospace; color:#e2e8f0; overflow:hidden; flex:1; }
.eval-flow { padding:12px 18px; background:#0e1526; border-top:1px solid #1e293b; display:flex; gap:10px; }
.flow-pill.pass { padding:5px 12px; border-radius:6px; font-size:14px; font-weight:700; background:rgba(34,197,94,0.18); color:#22c55e; border:1px solid rgba(34,197,94,0.35); }
.terminal-mini { background:#0a0e17; border:1px solid #1e293b; border-radius:14px; overflow:hidden; display:flex; flex-direction:column; }
.term-lines { padding:20px 24px; font-family:"JetBrains Mono",monospace; line-height:1.75; flex:1; display:flex; flex-direction:column; justify-content:space-between; }
.t-line { color:#f8fafc; } .t-prompt { color:#4ade80; font-weight:bold; } .t-cyan { color:#38bdf8; font-weight:bold; } .t-yellow { color:#fbbf24; font-weight:bold; } .t-green { color:#22c55e; font-weight:bold; } .t-red { color:#ef4444; font-weight:bold; } .t-indent { padding-left:22px; }
.t-banner-pass { margin-top:10px; padding:10px 16px; background:rgba(34,197,94,0.18); border:1px solid rgba(34,197,94,0.45); border-radius:8px; color:#22c55e; font-weight:800; font-size:18px; text-align:center; }
.t-banner-fail { margin-top:10px; padding:10px 16px; background:rgba(239,68,68,0.18); border:1px solid rgba(239,68,68,0.45); border-radius:8px; color:#ef4444; font-weight:800; font-size:18px; text-align:center; }
.terminal-window { background:#0a0e17; border:1px solid #1e293b; border-radius:14px; overflow:hidden; display:flex; flex-direction:column; }
.terminal-content { padding:20px 26px; font-family:"JetBrains Mono",monospace; flex:1; display:flex; flex-direction:column; justify-content:space-between; }
.cmd { color:#f8fafc; font-weight:bold; } .pass { color:#22c55e; font-weight:bold; } .success-banner { color:#22c55e; font-weight:bold; font-size:18px; margin-top:8px; }
.code-pill { display:inline-block; padding:8px 14px; background:#030712; border:1px solid #334155; border-radius:8px; font-family:monospace; color:#38bdf8; }
.footer { display:flex; justify-content:space-between; align-items:center; border-top:1px solid rgba(148,163,184,0.2); padding-top:14px; font-size:17px; color:#64748b; }
.footer-brand { font-weight:bold; color:#94a3b8; }
</style></head>
<body>
  __BODY__
  <div class="footer">
    <div class="footer-brand">Reactive Omni Sentinel: DoraHacks Reactive Omni Buildathon</div>
    <div>github.com/manderson240/reactive-omni-agent</div>
  </div>
</body></html>"""


def _synthesize_audio(text: str, output_mp3: Path) -> None:
    pocket_bin = shutil.which("pocket-tts") or "/home/mike-anderson/.local/bin/pocket-tts"
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    with tempfile.TemporaryDirectory() as td:
        wavs: list[Path] = []
        for idx, sent in enumerate(sentences):
            wav = Path(td) / f"part_{idx}.wav"
            subprocess.run(
                [pocket_bin, "generate", "--text", sent, "--device", "cpu", "--quantize", "--max-tokens", "150", "--output-path", str(wav), "-q"],
                check=True,
                capture_output=True,
            )
            if wav.exists() and wav.stat().st_size > 1000:
                wavs.append(wav)
        clist = Path(td) / "list.txt"
        clist.write_text("\n".join(f"file '{w}'" for w in wavs), encoding="utf-8")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(clist), "-af", "apad=pad_dur=1.25", "-c:a", "libmp3lame", "-b:a", "192k", str(output_mp3)],
            check=True,
            capture_output=True,
        )


def main() -> None:
    out_mp4 = REPO_ROOT / "docs" / "reactive_omni_pitch_demo.mp4"
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        parts: list[Path] = []
        for scene in SCENES:
            sid = scene["id"]
            print(f"🎬 Rendering {sid} at {WIDTH}x{HEIGHT} QHD...")
            html_file = work / f"{sid}.html"
            raw_png = work / f"{sid}_raw.png"
            png_file = work / f"{sid}.png"
            mp3_file = work / f"{sid}.mp3"
            seg_mp4 = work / f"{sid}.mp4"
            html_file.write_text(HTML_TEMPLATE.replace("__BODY__", scene["html_body"]), encoding="utf-8")
            subprocess.run(
                ["google-chrome", "--headless", "--hide-scrollbars", "--disable-gpu", "--force-device-scale-factor=1", f"--screenshot={raw_png}", f"--window-size={WIDTH},{CHROME_CAPTURE_HEIGHT}", str(html_file)],
                check=True,
                capture_output=True,
            )
            Image.open(raw_png).crop((0, 0, WIDTH, HEIGHT)).save(png_file)
            _synthesize_audio(scene["narration"], mp3_file)
            subprocess.run(
                ["ffmpeg", "-y", "-loop", "1", "-i", str(png_file), "-i", str(mp3_file), "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", str(seg_mp4)],
                check=True,
                capture_output=True,
            )
            parts.append(seg_mp4)
        clist = work / "concat.txt"
        clist.write_text("\n".join(f"file '{p}'" for p in parts), encoding="utf-8")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(clist), "-c", "copy", str(out_mp4)], check=True, capture_output=True)
    info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "json", str(out_mp4)], text=True))
    print(f"GENERATED: {out_mp4} ({float(info['format']['duration']):.2f}s, {int(info['format']['size'])/(1024*1024):.2f} MB)")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"Elapsed: {time.time() - t0:.1f}s")
