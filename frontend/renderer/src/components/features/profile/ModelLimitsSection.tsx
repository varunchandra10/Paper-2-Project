import React, { useEffect, useState } from 'react';
import { API_BASE } from '../../../config/api';
import { IconActivity, IconLoader } from '../../ui/Icons';
import { ServerMetricsBadge } from './ServerMetricsBadge';
import { ProviderQuotaCard } from './ProviderQuotaCard';

interface LimitMetric {
  limit: number | string;
  used: number;
  remaining_pct: number;
  refresh_message: string;
  status: string;
}

export interface ProviderLimit {
  label: string;
  description: string;
  is_local: boolean;
  weekly: LimitMetric;
  five_hour: LimitMetric;
}

interface LimitsData {
  groq?: any;
  openrouter?: any;
  gemini?: any;
  huggingface?: any;
  local?: any;
}

export const ModelLimitsSection: React.FC = () => {
  const [limitsData, setLimitsData] = useState<LimitsData | null>(null);
  const [serverMetrics, setServerMetrics] = useState<any>(null);
  const [localModels, setLocalModels] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchLimits = async (showFullLoading = false) => {
    try {
      if (showFullLoading) setIsLoading(true);
      const [limitsRes, modelsRes] = await Promise.all([
        fetch(`${API_BASE}/models/limits`),
        fetch(`${API_BASE}/models`)
      ]);

      if (limitsRes.ok) {
        const data = await limitsRes.json();
        setLimitsData(data.limits || null);
        setServerMetrics(data.server_metrics || null);
      }

      if (modelsRes.ok) {
        const mData = await modelsRes.json();
        const localList = mData.groups?.local?.models || [];
        setLocalModels(localList.map((m: any) => m.id));
      }
    } catch (err) {
      console.error('Failed to fetch model limits in profile:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLimits(true);

    const handleRefresh = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent?.detail?.limits) {
        setLimitsData(customEvent.detail.limits);
      }
      fetchLimits(false);
    };

    window.addEventListener('refresh-model-limits', handleRefresh);

    // Poll model limits every 5 minutes (300,000ms)
    const intervalId = setInterval(() => {
      fetchLimits(false);
    }, 300000);

    return () => {
      window.removeEventListener('refresh-model-limits', handleRefresh);
      clearInterval(intervalId);
    };
  }, []);

  return (
    <div className="flex flex-col gap-4">
      {/* Header and Telemetry */}
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-mono font-bold text-[var(--accent)] uppercase tracking-wider flex items-center gap-2">
          <IconActivity className="text-xs" />
          <span>Model Rate Limits & Quotas</span>
        </h3>
        <button
          type="button"
          onClick={() => fetchLimits(true)}
          disabled={isLoading}
          className="text-[10px] font-mono text-[var(--accent)] hover:opacity-80 transition-opacity cursor-pointer disabled:opacity-50 flex items-center gap-1"
          title="Refresh limits data"
        >
          {isLoading && <IconLoader className="text-[10px] animate-spin" />}
          <span>{isLoading ? 'Updating...' : '↻ Refresh'}</span>
        </button>
      </div>

      <ServerMetricsBadge metrics={serverMetrics} />

      {/* Grid of Provider Quota Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3.5 items-stretch">
        {/* 1. Groq Models */}
        {(() => {
          const groqRem = serverMetrics?.groq?.remaining_requests;
          const groqLim = serverMetrics?.groq?.limit_requests || 1000;
          const groqReqPct = groqRem != null && groqLim > 0
            ? (groqRem < groqLim ? Math.min(99, Math.floor((groqRem / groqLim) * 100)) : 100)
            : 100;

          const groqTokRem = serverMetrics?.groq?.remaining_tokens;
          const groqTokLim = serverMetrics?.groq?.limit_tokens || 8000;
          const groqTokPct = groqTokRem != null && groqTokLim > 0
            ? (groqTokRem < groqTokLim ? Math.min(99, Math.floor((groqTokRem / groqTokLim) * 100)) : 100)
            : 100;

          return (
            <ProviderQuotaCard
              title="GROQ Models"
              tooltip="Live Groq Cloud LPU gateway metrics"
              primaryMetric={{
                label: "Daily Requests Remaining",
                refreshMessage: groqRem != null
                  ? `${groqRem.toLocaleString()} of ${groqLim.toLocaleString()} requests left today.`
                  : '1,000 requests/day available.',
                remainingPct: groqReqPct,
              }}
              secondaryMetric={{
                label: "Tokens Per Minute (TPM)",
                refreshMessage: groqTokRem != null
                  ? `${groqTokRem.toLocaleString()} / ${groqTokLim.toLocaleString()} TPM (Reset: ${serverMetrics?.groq?.reset_requests || 'rolling 60s'}).`
                  : '8,000 Tokens/min rate limit.',
                remainingPct: groqTokPct,
              }}
              consoleBadge={{
                text: "Qwen 3.8 27B • GPT-OSS 120B",
                subtext: "Groq LPU",
              }}
            />
          );
        })()}

        {/* 2. OpenRouter Models */}
        {(() => {
          const orWeekly = limitsData?.openrouter?.weekly;
          const orRemPct = orWeekly?.remaining_pct != null
            ? orWeekly.remaining_pct
            : (orWeekly?.limit && orWeekly?.used != null
                ? Math.max(0, Math.min(100, Math.round(((orWeekly.limit - orWeekly.used) / orWeekly.limit) * 100)))
                : 100);

          const orRefreshMsg = orWeekly?.refresh_message
            || (orWeekly?.limit ? `${orWeekly.limit - (orWeekly.used || 0)} of ${orWeekly.limit} free calls remaining.` : '200 of 200 free calls daily on :free models.');

          return (
            <ProviderQuotaCard
              title="OpenRouter Models"
              tooltip="OpenRouter Free Tier Models (Gemini 2.5 Flash & DeepSeek R1)"
              primaryMetric={{
                label: "Daily Free Tier Allowance",
                refreshMessage: orRefreshMsg,
                remainingPct: orRemPct,
              }}
              secondaryMetric={{
                label: "Official Console Usage",
                refreshMessage: serverMetrics?.openrouter?.usage != null
                  ? `$${Number(serverMetrics.openrouter.usage).toFixed(4)} total credit consumed.`
                  : '$0.0000 credit used.',
                valueDisplay: serverMetrics?.openrouter?.usage != null
                  ? `$${Number(serverMetrics.openrouter.usage).toFixed(4)}`
                  : '$0.0000',
              }}
              consoleBadge={{
                text: "Gemini 2.5 Flash • DeepSeek R1",
                subtext: "OpenRouter Free",
              }}
            />
          );
        })()}

        {/* 3. Google Gemini (Backend Dual-Engine) */}
        <ProviderQuotaCard
          title="Google Gemini"
          tooltip="Google AI Studio 1,500 reqs/day, 15 reqs/min for paper extraction & synthesis"
          primaryMetric={{
            label: "Daily Quota (1500 reqs/day)",
            refreshMessage: `${limitsData?.gemini?.daily_remaining ?? 1500} of 1,500 daily requests remaining.`,
            remainingPct: limitsData?.gemini?.daily_pct ?? 100,
          }}
          secondaryMetric={{
            label: "Per-Minute RPM Limit (15 RPM)",
            refreshMessage: `${limitsData?.gemini?.minute_remaining ?? 15} of 15 requests/min currently available.`,
            remainingPct: limitsData?.gemini?.minute_limit
              ? Math.round(((limitsData.gemini.minute_remaining ?? 15) / limitsData.gemini.minute_limit) * 100)
              : 100,
          }}
          consoleBadge={{
            text: "gemini-2.0-flash (Active)",
            subtext: "Paper Extraction",
          }}
        />

        {/* 4. Hugging Face Serverless Router */}
        <ProviderQuotaCard
          title="Hugging Face"
          tooltip="Hugging Face Serverless Router for PyTorch Architecture Synthesis"
          primaryMetric={{
            label: "Daily Code Quota",
            refreshMessage: `${limitsData?.huggingface?.daily_remaining ?? 5000} of ${limitsData?.huggingface?.daily_limit ?? 5000} requests remaining.`,
            remainingPct: limitsData?.huggingface?.daily_pct ?? 100,
          }}
          secondaryMetric={{
            label: "Dedicated Model",
            refreshMessage: "Qwen 2.5 Coder 32B Instruct (PyTorch Synthesis).",
            valueDisplay: "Active",
          }}
          consoleBadge={{
            text: serverMetrics?.huggingface?.username ? `@${serverMetrics.huggingface.username}` : "HF Router v1",
            subtext: "Code Engine",
          }}
        />

        {/* 5. Local Ollama Daemon */}
        <ProviderQuotaCard
          title="Local Ollama"
          tooltip="Local hardware inference running offline with zero external token consumption"
          primaryMetric={{
            label: "Hardware Compute Bounds",
            refreshMessage: localModels.length > 0
              ? `${localModels.length} local model(s) pulled & available.`
              : '100% offline availability.',
            valueDisplay: localModels.length > 0 ? `${localModels.length} Models` : '0 Models',
          }}
          secondaryMetric={{
            label: "Local Hardware Status",
            refreshMessage: localModels.length > 0
              ? `Loaded: ${localModels.slice(0, 2).join(', ')}`
              : 'Local Ollama Daemon Online',
            valueDisplay: localModels.length > 0 ? 'Online' : 'Offline',
          }}
          consoleBadge={{
            text: localModels.length > 0 ? localModels[0] : 'qwen2.5-coder:1.5b',
            subtext: "Offline Hardware",
          }}
        />
      </div>
    </div>
  );
};
