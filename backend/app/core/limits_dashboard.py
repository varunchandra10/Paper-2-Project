import os
import time
from typing import Dict, Any
from app.core.config import settings
from app.core.quota_tracker import quota_tracker



DASHBOARD_SCRIPT_JS = """
  <script>
    async function fetchLiveMetrics() {
      const icon = document.getElementById('refresh-icon');
      const statusEl = document.getElementById('sync-status');
      
      if (icon) icon.style.animation = 'spin 1s linear infinite';
      
      try {
        let res = await fetch('/models/limits');
        if (!res.ok) res = await fetch('/api/v1/models/limits');
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        
        const sm = data.server_metrics || {};
        const lim = data.limits || {};
        
        // 1. Gemini
        const gemStat = lim.gemini || {};
        const gemRem = gemStat.daily_remaining != null ? gemStat.daily_remaining : 1500;
        const gemUsed = gemStat.daily_used != null ? gemStat.daily_used : 0;
        const gemPct = gemStat.daily_pct != null ? gemStat.daily_pct : 100;
        
        const gemNumEl = document.getElementById('gem-numbers');
        if (gemNumEl) gemNumEl.innerText = gemRem.toLocaleString() + ' / 1,500';
        const gemSubEl = document.getElementById('gem-sub');
        if (gemSubEl) gemSubEl.innerHTML = 'remaining today &bull; ' + gemUsed + ' used';
        const gemBarEl = document.getElementById('gem-bar');
        if (gemBarEl) gemBarEl.style.width = Math.max(0, Math.min(100, gemPct)) + '%';
        
        // 2. Hugging Face Router
        const hfStat = lim.huggingface || {};
        const hfRem = hfStat.daily_remaining != null ? hfStat.daily_remaining : 5000;
        const hfLim = hfStat.daily_limit != null ? hfStat.daily_limit : 5000;
        const hfUsed = hfStat.daily_used != null ? hfStat.daily_used : 0;
        const hfPct = hfStat.daily_pct != null ? hfStat.daily_pct : 100;
        const hfNumEl = document.getElementById('hf-numbers');
        if (hfNumEl) hfNumEl.innerText = hfRem.toLocaleString() + ' / ' + hfLim.toLocaleString();
        const hfSubEl = document.getElementById('hf-sub');
        if (hfSubEl) hfSubEl.innerHTML = 'remaining today &bull; ' + hfUsed + ' used';
        const hfBarEl = document.getElementById('hf-bar');
        if (hfBarEl) hfBarEl.style.width = Math.max(0, Math.min(100, hfPct)) + '%';
        
        // 3. Groq
        const groqServer = sm.groq || {};
        const groqRem = groqServer.remaining_requests != null ? groqServer.remaining_requests : 1000;
        const groqLim = groqServer.limit_requests != null ? Math.max(1, groqServer.limit_requests) : 1000;
        const groqTok = groqServer.remaining_tokens != null ? groqServer.remaining_tokens : 8000;
        const groqTokLim = groqServer.limit_tokens != null ? groqServer.limit_tokens : 8000;
        const groqReset = groqServer.reset_requests || 'Rolling 24h';
        const groqPct = Math.max(0, Math.min(100, Math.round((groqRem / groqLim) * 100)));
        
        const groqNumEl = document.getElementById('groq-numbers');
        if (groqNumEl) groqNumEl.innerText = groqRem.toLocaleString() + ' / ' + groqLim.toLocaleString();
        const groqBarEl = document.getElementById('groq-bar');
        if (groqBarEl) groqBarEl.style.width = groqPct + '%';
        const groqTokEl = document.getElementById('groq-tokens-info');
        if (groqTokEl) groqTokEl.innerText = 'Tokens: ' + groqTok.toLocaleString() + ' / ' + groqTokLim.toLocaleString() + ' TPM • Reset: ' + groqReset;
        
        // 4. OpenRouter
        const orServer = sm.openrouter || {};
        const orUsage = orServer.usage != null ? Number(orServer.usage).toFixed(4) : '0.0000';
        const orPct = (lim.openrouter && lim.openrouter.weekly && lim.openrouter.weekly.remaining_pct != null) ? lim.openrouter.weekly.remaining_pct : 100;
        const orNumEl = document.getElementById('or-numbers');
        if (orNumEl) orNumEl.innerText = '$' + orUsage;
        const orBarEl = document.getElementById('or-bar');
        if (orBarEl) orBarEl.style.width = orPct + '%';
        
        // 5. Local
        const localServer = sm.local || {};
        const localModels = localServer.models || [];
        const localInfoEl = document.getElementById('local-info');
        if (localInfoEl) {
          localInfoEl.innerText = localModels.length > 0 ? 'Online (' + localModels.slice(0, 2).join(', ') + ')' : (localServer.status === 'offline' ? 'Offline' : '100% Available');
        }
        
        const now = new Date();
        const timeStr = now.toTimeString().split(' ')[0];
        if (statusEl) statusEl.innerText = '● Live Telemetry: Synced (' + timeStr + ')';
      } catch (err) {
        console.warn('Failed to refresh live metrics:', err);
        if (statusEl) statusEl.innerText = '⚠️ Telemetry Sync Paused';
      } finally {
        if (icon) icon.style.animation = 'none';
      }
    }
    
    // Auto-poll live telemetry every 10 seconds
    setInterval(fetchLiveMetrics, 10000);
  </script>
"""


def get_limits_json_payload() -> Dict[str, Any]:
    """Returns a unified, clean JSON payload of provider rate limits and live console telemetry."""
    summary = quota_tracker.get_limits_summary()
    server_metrics = quota_tracker.fetch_live_server_metrics()
    return {
        "status": "success",
        "timestamp": int(time.time()),
        "limits": summary,
        "server_metrics": server_metrics
    }


def generate_limits_html_dashboard() -> str:
    """Generates a clean, live rate limits dashboard powered directly by official provider gateway metrics."""
    # 1. Fetch live metrics directly from official API gateways & consoles via unified payload
    payload = get_limits_json_payload()
    summary = payload["limits"]
    server_metrics = payload["server_metrics"]
    
    has_gemini = settings.has_gemini()
    has_hf = settings.has_huggingface()
    has_groq = settings.has_groq()
    has_or = settings.has_openrouter()

    # Provider 1: Gemini (Backend Paper Extraction & Code Synthesis) - math precomputed in quota_tracker
    gem_stat = summary.get("gemini") or {}
    gem_remaining = gem_stat.get("daily_remaining", 1500)
    gem_used = gem_stat.get("daily_used", 0)
    gem_pct = gem_stat.get("daily_pct", 100)

    # Provider 2: Hugging Face (Backend PyTorch Architecture Synthesis) - math precomputed in quota_tracker
    hf_stat = summary.get("huggingface") or {}
    hf_limit = hf_stat.get("daily_limit", 5000)
    hf_remaining = hf_stat.get("daily_remaining", 5000)
    hf_used = hf_stat.get("daily_used", 0)
    hf_pct = hf_stat.get("daily_pct", 100)

    # Provider 3: Groq (From Live Response Headers & Quota Tracker Summary)
    groq_stat = (summary.get("groq") or {}).get("weekly") or {}
    groq_server = server_metrics.get("groq") or {}
    groq_limit_safe = groq_stat.get("limit", 1000)
    groq_pct = groq_stat.get("remaining_pct", 100)
    groq_rem_req = groq_server.get("remaining_requests", max(0, groq_limit_safe - groq_stat.get("used", 0)))
    groq_reset = groq_server.get("reset_requests") or "Rolling 24h"
    groq_tokens = groq_server.get("remaining_tokens", 8000)
    groq_tok_lim = groq_server.get("limit_tokens", 8000)

    # Provider 4: OpenRouter (From Official Console API & Quota Tracker Summary)
    or_server = server_metrics.get("openrouter") or {}
    try:
        or_usage = float(or_server.get("usage", 0.0) or 0.0)
    except (ValueError, TypeError):
        or_usage = 0.0
    or_w = (summary.get("openrouter") or {}).get("weekly") or {}
    or_pct = or_w.get("remaining_pct", 100)

    # Provider 5: Local Ollama (From Local Daemon)
    local_server = server_metrics.get("local") or {}
    local_models = local_server.get("models") or []
    local_status = "Online (" + ", ".join(local_models[:2]) + ")" if local_models else ("Offline" if local_server.get("status") == "offline" else "100% Available")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Live Model Quotas & Rate Limits | RUEXIS AI</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --emerald: #10b981;
      --sky: #38bdf8;
      --amber: #f59e0b;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Inter', sans-serif;
      padding: 32px 16px;
      display: flex;
      justify-content: center;
    }}
    .wrap {{
      max-width: 860px;
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border);
      padding-bottom: 16px;
    }}
    .logo {{
      font-size: 18px;
      font-weight: 700;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .badge {{
      font-size: 10px;
      font-family: 'IBM Plex Mono', monospace;
      padding: 3px 8px;
      border-radius: 6px;
      font-weight: 600;
    }}
    .badge-on {{ background: rgba(16, 185, 129, 0.15); color: var(--emerald); border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-off {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
    
    .section-title {{
      font-size: 13px;
      font-weight: 700;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 12px;
      font-family: 'IBM Plex Mono', monospace;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 14px;
    }}
    .grid-3 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 14px;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .card-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .card-name {{
      font-size: 15px;
      font-weight: 600;
    }}
    .source-tag {{
      font-size: 10px;
      font-family: 'IBM Plex Mono', monospace;
      color: var(--sky);
      background: rgba(56, 189, 248, 0.1);
      padding: 1px 6px;
      border-radius: 4px;
      display: inline-block;
      margin-top: 2px;
    }}
    .limit-number {{
      font-size: 22px;
      font-weight: 700;
      font-family: 'IBM Plex Mono', monospace;
      color: var(--text);
    }}
    .limit-label {{
      font-size: 12px;
      color: var(--muted);
    }}
    .bar {{
      height: 6px;
      background: #0f172a;
      border-radius: 99px;
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      background: var(--emerald);
      border-radius: 99px;
    }}
    .reset-info {{
      font-size: 11.5px;
      color: var(--muted);
      display: flex;
      align-items: center;
      gap: 6px;
      border-top: 1px solid rgba(255,255,255,0.06);
      padding-top: 10px;
    }}
    .simple-banner {{
      background: rgba(16, 185, 129, 0.08);
      border: 1px solid rgba(16, 185, 129, 0.25);
      border-radius: 10px;
      padding: 12px 16px;
      font-size: 13px;
      line-height: 1.5;
      color: #a7f3d0;
    }}
    footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      font-family: 'IBM Plex Mono', monospace;
      color: var(--muted);
      border-top: 1px solid var(--border);
      padding-top: 16px;
    }}
    a {{ color: var(--emerald); text-decoration: none; }}
    @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
  </style>
</head>
<body>

  <div class="wrap">
    
    <!-- Header -->
    <header>
      <div class="logo">
        <span style="color: var(--emerald);">●</span>
        <span>RUEXIS AI &bull; Live Provider Console Metrics</span>
      </div>
      <div style="display: flex; align-items: center; gap: 12px;">
        <span id="sync-status" style="font-size: 11px; color: var(--emerald); font-family: 'IBM Plex Mono', monospace;">● Live Telemetry: ACTIVE</span>
        <button id="refresh-btn" onclick="fetchLiveMetrics()" style="background: rgba(16, 185, 129, 0.15); color: var(--emerald); border: 1px solid rgba(16, 185, 129, 0.3); padding: 4px 10px; border-radius: 6px; font-family: 'IBM Plex Mono', monospace; font-size: 11px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px;">
          <span id="refresh-icon" style="display: inline-block;">↻</span> Refresh
        </button>
      </div>
    </header>

    <!-- Simple Banner -->
    <div class="simple-banner">
      ⚡ <strong>Active Models in Use:</strong>
      Displaying live telemetry for active engines: <strong>Google Gemini</strong>, <strong>Hugging Face Router</strong>, <strong>Groq Cloud</strong>, <strong>OpenRouter</strong>, and <strong>Local Ollama</strong>.
    </div>

    <!-- Group 1: Code Generation -->
    <div>
      <div class="section-title">1. Code Generation Models (Dedicated Backend Engines)</div>
      
      <div class="grid-2">
        <!-- Gemini Card -->
        <div class="card">
          <div class="card-top">
            <div>
              <div class="card-name">Google Gemini 2.0 Flash</div>
              <div class="source-tag">Paper Extraction & Code Synthesis</div>
            </div>
            <span class="badge {'badge-on' if has_gemini else 'badge-off'}">{'READY' if has_gemini else 'KEY MISSING'}</span>
          </div>
          
          <div style="display: flex; align-items: baseline; gap: 6px;">
            <div id="gem-numbers" class="limit-number">{gem_remaining:,} / 1,500</div>
            <div id="gem-sub" class="limit-label">remaining today &bull; {gem_used} used</div>
          </div>
          
          <div class="bar">
            <div id="gem-bar" class="bar-fill" style="width: {gem_pct}%;"></div>
          </div>
          
          <div class="reset-info">
            <span>🕒 <strong>Reset:</strong> Daily quota resets at 00:00 UTC (15 RPM rolling)</span>
          </div>
        </div>

        <!-- Hugging Face Card -->
        <div class="card">
          <div class="card-top">
            <div>
              <div class="card-name">Hugging Face Serverless Router</div>
              <div class="source-tag">Qwen 2.5 Coder 32B &bull; PyTorch Synthesis</div>
            </div>
            <span class="badge {'badge-on' if has_hf else 'badge-off'}">{'READY' if has_hf else 'KEY MISSING'}</span>
          </div>
          
          <div style="display: flex; align-items: baseline; gap: 6px;">
            <div id="hf-numbers" class="limit-number">{hf_remaining:,} / {hf_limit:,}</div>
            <div id="hf-sub" class="limit-label">remaining today &bull; {hf_used} used</div>
          </div>
          
          <div class="bar">
            <div id="hf-bar" class="bar-fill" style="width: {hf_pct}%; background: var(--sky);"></div>
          </div>
          
          <div class="reset-info">
            <span>⚡ <strong>Engine:</strong> Dedicated PyTorch Code Generation (v1 Router)</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Group 2: Chat Models -->
    <div>
      <div class="section-title">2. Conversational Chat Models (Official Console Stats)</div>
      
      <div class="grid-3">
        <!-- Groq -->
        <div class="card">
          <div class="card-top">
            <div>
              <div class="card-name">Groq LPUs</div>
              <div class="source-tag">Qwen 3.8 27B &bull; GPT-OSS 120B</div>
            </div>
            <span class="badge {'badge-on' if has_groq else 'badge-off'}">{'READY' if has_groq else 'OFF'}</span>
          </div>
          <div style="display: flex; align-items: baseline; gap: 6px;">
            <div id="groq-numbers" class="limit-number">{groq_rem_req:,} / {groq_limit_safe:,}</div>
            <div class="limit-label">requests left today</div>
          </div>
          <div class="bar">
            <div id="groq-bar" class="bar-fill" style="width: {groq_pct}%;"></div>
          </div>
          <div id="groq-tokens-info" class="reset-info">Tokens: {groq_tokens:,} / {groq_tok_lim:,} TPM &bull; Reset: {groq_reset}</div>
        </div>

        <!-- OpenRouter -->
        <div class="card">
          <div class="card-top">
            <div>
              <div class="card-name">OpenRouter</div>
              <div class="source-tag">Gemini 2.5 Flash &bull; DeepSeek R1</div>
            </div>
            <span class="badge {'badge-on' if has_or else 'badge-off'}">{'READY' if has_or else 'OFF'}</span>
          </div>
          <div style="display: flex; align-items: baseline; gap: 6px;">
            <div id="or-numbers" class="limit-number">${or_usage:.4f}</div>
            <div class="limit-label">credit used &bull; 200/day free</div>
          </div>
          <div class="bar">
            <div id="or-bar" class="bar-fill" style="width: {or_pct}%; background: var(--amber);"></div>
          </div>
          <div class="reset-info">Rate Limit: 20 requests / 10s</div>
        </div>

        <!-- Local Ollama -->
        <div class="card">
          <div class="card-top">
            <div>
              <div class="card-name">Local Ollama</div>
              <div class="source-tag">Source: Local Ollama Daemon</div>
            </div>
            <span class="badge badge-on">UNLIMITED</span>
          </div>
          <div style="display: flex; align-items: baseline; gap: 6px;">
            <div class="limit-number">100%</div>
            <div class="limit-label">offline privacy</div>
          </div>
          <div class="bar">
            <div class="bar-fill" style="width: 100%;"></div>
          </div>
          <div id="local-info" class="reset-info">{local_status}</div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer>
      <span>RUEXIS AI Platform Backend &bull; Direct Provider Telemetry</span>
      <div>
        <a href="/docs" target="_blank">Swagger API</a> &bull;
        <a href="/api/v1/models/limits" target="_blank">Raw Limits JSON</a>
      </div>
    </footer>

  </div>

  {DASHBOARD_SCRIPT_JS}
</body>
</html>
"""
    return html
