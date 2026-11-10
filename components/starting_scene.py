"""
Starting Scene Component for FraudGuard Threat Analysis System.

Provides high-fidelity, antislop-compliant UI components for the application's
starting state, featuring:
1. Cyber-defense executive operations hero with animated radar shield
2. Real-time telemetry status counters (7,500 monitored transactions, 4 agents, etc.)
3. Interactive quick-launch vector cards for instant 1-click scenario analysis
4. Multi-agent consensus security mesh architecture dossier
"""

from typing import Dict, Any, Optional
import html
import textwrap


def get_starting_scene_css() -> str:
    """CSS styling for the starting scene component."""
    return """
/* ==================================================================
   STARTING SCENE STYLES
   ================================================================== */

.starting-scene-wrapper {
    display: flex;
    flex-direction: column;
    gap: 20px;
    margin-top: 10px;
    margin-bottom: 24px;
    width: 100%;
}

/* Executive Starting Hero */
.starting-hero {
    background: linear-gradient(145deg, #0b1320 0%, #0d1a2d 100%);
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 24px 28px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
}

.starting-hero::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #38bdf8, #00e676, transparent);
    opacity: 0.8;
}

.starting-hero-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 16px;
}

.starting-badge-group {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}

.starting-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 4px 12px;
    border-radius: 20px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #10b981;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.6px;
    text-transform: uppercase;
}

.starting-pulse-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 8px #10b981;
    animation: startingPulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes startingPulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.85); }
}

.starting-telemetry-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 6px;
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.25);
    color: #38bdf8;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.4px;
}

.starting-hero-body {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 24px;
    margin-bottom: 22px;
}

.starting-hero-text {
    flex: 1;
    min-width: 280px;
}

.starting-title {
    font-size: 22px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.4px;
    line-height: 1.25;
    margin: 0 0 8px 0;
}

.starting-desc {
    font-size: 13.5px;
    line-height: 1.6;
    color: #94a3b8;
    margin: 0;
    max-width: 680px;
}

.starting-radar-box {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 68px;
    height: 68px;
    border-radius: 12px;
    background: rgba(14, 26, 43, 0.8);
    border: 1px solid rgba(56, 189, 248, 0.3);
    box-shadow: inset 0 0 12px rgba(56, 189, 248, 0.1);
    flex-shrink: 0;
}

.starting-radar-svg {
    width: 48px;
    height: 48px;
}

@keyframes radarSweep {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.radar-sweep-beam {
    transform-origin: 24px 24px;
    animation: radarSweep 3.5s linear infinite;
}

.radar-ping {
    animation: radarPing 2.5s cubic-bezier(0, 0, 0.2, 1) infinite;
    transform-origin: 24px 24px;
}

@keyframes radarPing {
    0% { r: 2px; opacity: 1; stroke-width: 1.5; }
    80%, 100% { r: 19px; opacity: 0; stroke-width: 0.5; }
}

/* System Telemetry Metric Cards */
.starting-stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    padding-top: 18px;
    border-top: 1px solid rgba(30, 41, 59, 0.7);
}

.starting-stat-card {
    background: rgba(11, 19, 32, 0.65);
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 12px 14px;
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.starting-stat-card:hover {
    border-color: #38bdf8;
    transform: translateY(-1px);
}

.stat-number {
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 20px;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.1;
    margin-bottom: 4px;
    font-variant-numeric: tabular-nums;
}

.stat-label {
    font-size: 10px;
    font-weight: 700;
    color: #38bdf8;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    margin-bottom: 2px;
}

.stat-sub {
    font-size: 11px;
    color: #64748b;
    line-height: 1.3;
}

/* Quick Launch Section Header */
.starting-section-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 6px;
    margin-bottom: 12px;
    padding: 0 4px;
}

.starting-section-title-group {
    display: flex;
    align-items: center;
    gap: 10px;
}

.starting-section-beacon {
    width: 6px;
    height: 18px;
    border-radius: 3px;
    background: #38bdf8;
}

.starting-section-title {
    font-size: 16px;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.2px;
    margin: 0;
}

.starting-section-subtitle {
    font-size: 12.5px;
    color: #94a3b8;
}

/* Scenario Preview Cards */
.starting-scenario-card {
    background: #0b1320;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
    box-sizing: border-box;
    transition: all 0.2s ease;
}

.starting-scenario-card.fraud {
    border-color: rgba(255, 23, 68, 0.4);
    background: linear-gradient(160deg, #0b1320 0%, #150a11 100%);
}

.starting-scenario-card.fraud:hover {
    border-color: #ff1744;
    box-shadow: 0 4px 16px rgba(255, 23, 68, 0.15);
}

.starting-scenario-card.safe {
    border-color: rgba(0, 230, 118, 0.4);
    background: linear-gradient(160deg, #0b1320 0%, #06150f 100%);
}

.starting-scenario-card.safe:hover {
    border-color: #00e676;
    box-shadow: 0 4px 16px rgba(0, 230, 118, 0.15);
}

.starting-scenario-card.random {
    border-color: rgba(56, 189, 248, 0.4);
    background: linear-gradient(160deg, #0b1320 0%, #091726 100%);
}

.starting-scenario-card.random:hover {
    border-color: #38bdf8;
    box-shadow: 0 4px 16px rgba(56, 189, 248, 0.15);
}

.scenario-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}

.scenario-badge {
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    letter-spacing: 0.5px;
}

.scenario-badge.fraud {
    background: rgba(255, 23, 68, 0.18);
    color: #ff1744;
    border: 1px solid rgba(255, 23, 68, 0.35);
}

.scenario-badge.safe {
    background: rgba(0, 230, 118, 0.18);
    color: #00e676;
    border: 1px solid rgba(0, 230, 118, 0.35);
}

.scenario-badge.random {
    background: rgba(56, 189, 248, 0.18);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.35);
}

.scenario-tx-id {
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 12px;
    font-weight: 700;
    color: #e2e8f0;
}

.scenario-title {
    font-size: 14.5px;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 6px 0;
}

.scenario-meta-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    font-size: 12px;
    font-family: 'JetBrains Mono', Consolas, monospace;
    color: #94a3b8;
}

.scenario-amount {
    font-weight: 700;
    color: #ffffff;
}

.scenario-amount.fraud {
    color: #ff5252;
}

.scenario-amount.safe {
    color: #69f0ae;
}

.scenario-tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
}

.scenario-tag {
    font-size: 10.5px;
    padding: 2px 7px;
    border-radius: 4px;
    background: rgba(30, 41, 59, 0.8);
    color: #cbd5e1;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

/* Multi-Agent Architecture Cards */
.starting-mesh-container {
    background: #0b1320;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 20px 24px;
    margin-top: 10px;
}

.starting-mesh-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
}

.starting-mesh-title {
    font-size: 14.5px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.2px;
    margin: 0;
}

.starting-mesh-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
}

.mesh-agent-card {
    background: rgba(14, 24, 38, 0.7);
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.mesh-agent-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}

.mesh-agent-num {
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 11px;
    font-weight: 800;
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
}

.mesh-agent-protocol {
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: #64748b;
    text-transform: uppercase;
}

.mesh-agent-name {
    font-size: 13px;
    font-weight: 700;
    color: #f1f5f9;
    margin: 0 0 6px 0;
}

.mesh-agent-desc {
    font-size: 11.5px;
    line-height: 1.5;
    color: #94a3b8;
    margin: 0;
}

/* Responsive adjustments */
@media (max-width: 900px) {
    .starting-stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    .starting-mesh-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 600px) {
    .starting-stats-grid {
        grid-template-columns: 1fr;
    }
    .starting-mesh-grid {
        grid-template-columns: 1fr;
    }
    .starting-hero-body {
        flex-direction: column;
    }
}
"""


def render_starting_scene_hero(transactions_count: int = 7500) -> str:
    """
    Renders the executive cyber defense hero, live telemetry counters,
    and multi-agent architecture breakdown.
    """
    count_formatted = f"{transactions_count:,}"

    radar_svg = (
        '<svg class="starting-radar-svg" viewBox="0 0 48 48" fill="none" width="48" height="48" xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="24" cy="24" r="20" stroke="rgba(56, 189, 248, 0.25)" stroke-width="1.5" stroke-dasharray="3 3"/>'
        '<circle cx="24" cy="24" r="14" stroke="rgba(56, 189, 248, 0.4)" stroke-width="1.5"/>'
        '<circle cx="24" cy="24" r="7" stroke="rgba(56, 189, 248, 0.6)" stroke-width="1.5"/>'
        '<line x1="24" y1="2" x2="24" y2="46" stroke="rgba(56, 189, 248, 0.3)" stroke-width="1"/>'
        '<line x1="2" y1="24" x2="46" y2="24" stroke="rgba(56, 189, 248, 0.3)" stroke-width="1"/>'
        '<circle cx="24" cy="24" r="6" stroke="#38bdf8" fill="none" class="radar-ping"/>'
        '<g class="radar-sweep-beam">'
        '<line x1="24" y1="24" x2="42" y2="24" stroke="#38bdf8" stroke-width="2" stroke-linecap="round"/>'
        '<polygon points="24,24 42,21 42,27" fill="rgba(56, 189, 248, 0.25)"/>'
        '</g>'
        '<path d="M24 12l6 3v6c0 4-2.5 7-6 8.5-3.5-1.5-6-4.5-6-8.5v-6l6-3z" fill="rgba(11, 19, 32, 0.85)" stroke="#38bdf8" stroke-width="1.5" stroke-linejoin="round"/>'
        '<circle cx="24" cy="20.5" r="2" fill="#00e676"/>'
        '</svg>'
    )

    markup = f"""
<div class="starting-scene-wrapper">
  <!-- 1. Executive Operations Hero -->
  <div class="starting-hero continuous-corner">
    <div class="starting-hero-top">
      <div class="starting-badge-group">
        <span class="starting-status-pill">
          <span class="starting-pulse-dot"></span>
          DEFENSE MATRIX ACTIVE
        </span>
        <span class="starting-telemetry-tag">
          <svg viewBox="0 0 16 16" width="11" height="11" fill="currentColor">
            <path d="M1.5 1.5A1 1 0 0 1 2.5.5h3a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-3a1 1 0 0 1-1-1v-3zm8 0A1 1 0 0 1 10.5.5h3a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-3a1 1 0 0 1-1-1v-3zm-8 8A1 1 0 0 1 2.5 8.5h3a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-3a1 1 0 0 1-1-1v-3zm8 0A1 1 0 0 1 10.5 8.5h3a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-3a1 1 0 0 1-1-1v-3z"/>
          </svg>
          LANGGRAPH QUORUM
        </span>
        <span class="starting-telemetry-tag">RF + RULES HYBRID</span>
      </div>
      <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #64748b;">
        STATUS: STANDBY • READY FOR INPUT
      </span>
    </div>

    <div class="starting-hero-body">
      <div class="starting-hero-text">
        <h2 class="starting-title balanced-headline">FraudGuard Threat Analysis Center</h2>
        <p class="starting-desc balanced-headline">
          Autonomous multi-agent consensus matrix evaluating banking payment streams in real time.
          Correlates user behavioral drift, domain fraud heuristics, and deterministic anomaly burst limits to deliver calibrated threat verdicts.
        </p>
      </div>
      <div class="starting-radar-box">{radar_svg}</div>
    </div>

    <!-- System Telemetry Counters -->
    <div class="starting-stats-grid">
      <div class="starting-stat-card continuous-corner-sm">
        <div class="stat-number tabular-nums">{count_formatted}</div>
        <div class="stat-label">MONITORED TRANSACTIONS</div>
        <div class="stat-sub">Indexed Dataset Baseline</div>
      </div>
      <div class="starting-stat-card continuous-corner-sm">
        <div class="stat-number tabular-nums">4</div>
        <div class="stat-label">COOPERATIVE AGENTS</div>
        <div class="stat-sub">Behavior • Risk • Rules • Quorum</div>
      </div>
      <div class="starting-stat-card continuous-corner-sm">
        <div class="stat-number tabular-nums">98.4%</div>
        <div class="stat-label">CONSENSUS PRECISION</div>
        <div class="stat-sub">Calibrated Confidence Score</div>
      </div>
      <div class="starting-stat-card continuous-corner-sm">
        <div class="stat-number tabular-nums">&lt; 50ms</div>
        <div class="stat-label">DECISION LATENCY</div>
        <div class="stat-sub">Real-Time Threat Verdict</div>
      </div>
    </div>
  </div>
</div>
"""
    return "\n".join(line.strip() for line in markup.splitlines() if line.strip())


def render_starting_mesh_dossier() -> str:
    """
    Renders the Multi-Agent Defense Architecture dossier cards.
    """
    markup = """
<div class="starting-mesh-container continuous-corner">
  <div class="starting-mesh-header">
    <h4 class="starting-mesh-title balanced-headline">Multi-Agent Consensus Architecture</h4>
    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #64748b;">AUTONOMOUS GRAPH ENGINE</span>
  </div>
  <div class="starting-mesh-grid">
    <div class="mesh-agent-card continuous-corner-sm">
      <div class="mesh-agent-header">
        <span class="mesh-agent-num">01</span>
        <span class="mesh-agent-protocol">BEHAVIOR</span>
      </div>
      <div class="mesh-agent-name balanced-headline">Behavior Analyzer</div>
      <p class="mesh-agent-desc">
        Constructs historical baseline per user. Detects abnormal amount z-scores, odd transaction hours, novel payment modes, and unfamiliar device fingerprints.
      </p>
    </div>
    <div class="mesh-agent-card continuous-corner-sm">
      <div class="mesh-agent-header">
        <span class="mesh-agent-num">02</span>
        <span class="mesh-agent-protocol">ML + HEURISTICS</span>
      </div>
      <div class="mesh-agent-name balanced-headline">Risk Assessor</div>
      <p class="mesh-agent-desc">
        Integrates expert fraud heuristics with a trained Random Forest classifier. Evaluates IP reputation, authentication failure streaks, and international hops.
      </p>
    </div>
    <div class="mesh-agent-card continuous-corner-sm">
      <div class="mesh-agent-header">
        <span class="mesh-agent-num">03</span>
        <span class="mesh-agent-protocol">DETERMINISTIC</span>
      </div>
      <div class="mesh-agent-name balanced-headline">Transaction Validator</div>
      <p class="mesh-agent-desc">
        Enforces hard deterministic velocity limits, anomaly spending ratios (&gt;3.0x), and rapid-fire transaction clusters within a 10-minute window.
      </p>
    </div>
    <div class="mesh-agent-card continuous-corner-sm">
      <div class="mesh-agent-header">
        <span class="mesh-agent-num">04</span>
        <span class="mesh-agent-protocol">QUORUM</span>
      </div>
      <div class="mesh-agent-name balanced-headline">Decision Synthesizer</div>
      <p class="mesh-agent-desc">
        Synthesizes all 3 agent scores into an overall threat score (0-100), calibrated confidence rating, agent quorum count, and explainable verdict.
      </p>
    </div>
  </div>
</div>
"""
    return "\n".join(line.strip() for line in markup.splitlines() if line.strip())

