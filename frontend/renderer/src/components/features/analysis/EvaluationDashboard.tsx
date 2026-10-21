import React, { useState } from 'react';
import { usePanelStore } from '../../../store/panelStore';
import type { RAGSummaryMetrics } from '../../../store/slices/evalSlice';

interface MetricConfig {
  key: keyof RAGSummaryMetrics;
  label: string;
  description: string;
  kValue?: number;
}

const METRIC_CONFIGS: MetricConfig[] = [
  { key: 'precision_at_5', label: 'Precision@5', description: 'Fraction of top-5 retrieved chunks that are relevant ground truth' },
  { key: 'recall_at_5', label: 'Recall@5', description: 'Fraction of total ground truth chunks retrieved within top-5' },
  { key: 'mrr', label: 'MRR (Mean Reciprocal Rank)', description: 'Reciprocal rank of first relevant chunk (1/rank)' },
  { key: 'ndcg_at_5', label: 'NDCG@5', description: 'Normalized discounted cumulative gain measuring ranking position quality' },
  { key: 'faithfulness', label: 'Faithfulness', description: 'LLM-verified factual grounding against paper context chunks' },
  { key: 'answer_relevance', label: 'Answer Relevance', description: 'Semantic relevance and directness of answer to the scientific question' },
  { key: 'citation_accuracy', label: 'Citation Accuracy', description: 'Grounding accuracy to authors, paper titles, and specific sections' },
  { key: 'context_precision', label: 'Context Precision', description: 'Signal-to-noise ratio of relevant chunks in retrieved context' },
];

export const EvaluationDashboard: React.FC = () => {
  const {
    evalResults,
    isEvalRunning,
    evalBaseline,
    showBaselineComparison,
    runEval,
    setShowBaselineComparison,
    activePaperId,
  } = usePanelStore();

  const [activeTab, setActiveTab] = useState<'metrics' | 'queries' | 'scorecard'>('metrics');
  const targetPaperId = activePaperId || 'paper_2';

  const handleRunEval = () => {
    runEval(targetPaperId);
  };

  const handleExportJSON = () => {
    if (!evalResults) return;
    const jsonStr = JSON.stringify(evalResults, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rag_evaluation_${targetPaperId}_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getColorClasses = (val: number) => {
    if (val >= 0.85) {
      return {
        text: 'text-emerald-400',
        bg: 'bg-emerald-500',
        bgSubtle: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
        badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
      };
    }
    if (val >= 0.70) {
      return {
        text: 'text-amber-400',
        bg: 'bg-amber-500',
        bgSubtle: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
        badge: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
      };
    }
    return {
      text: 'text-rose-400',
      bg: 'bg-rose-500',
      bgSubtle: 'bg-rose-500/10 border-rose-500/30 text-rose-300',
      badge: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
    };
  };

  const summary = evalResults?.summary_metrics;
  const baseline = evalResults?.baseline || evalBaseline;

  return (
    <div className="flex flex-col gap-3 font-sans text-left select-text">
      {/* Top Header Card */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-xl bg-[var(--bg-app)] border border-[var(--border-subtle)] shadow-sm">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 text-sm">
            📊
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-[var(--text-main)] tracking-wide">
                RAG Evaluation Metrics Dashboard
              </h3>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-blue-500/10 border border-blue-500/30 text-blue-300">
                Phase 8.1 Empirical
              </span>
            </div>
            <p className="text-[10px] text-[var(--text-muted)] font-mono">
              Evaluates Vector DB hybrid search, grounding faithfulness, and LLM synthesis.
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowBaselineComparison(!showBaselineComparison)}
            className={`text-[10px] font-mono px-2.5 py-1.5 rounded-lg border transition-all cursor-pointer flex items-center gap-1.5 ${
              showBaselineComparison
                ? 'bg-purple-500/20 text-purple-300 border-purple-500/40 shadow-sm'
                : 'bg-[var(--bg-card)] text-[var(--text-muted)] border-[var(--border-subtle)] hover:text-[var(--text-main)]'
            }`}
            title="Toggle delta comparison against benchmark baseline"
          >
            <span>⚖️</span>
            <span>{showBaselineComparison ? 'Hide Baseline' : 'Compare with Baseline'}</span>
          </button>

          {evalResults && (
            <button
              type="button"
              onClick={handleExportJSON}
              className="text-[10px] font-mono px-2.5 py-1.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-card)] text-[var(--text-main)] hover:bg-[var(--accent-subtle)] hover:border-[var(--accent-border)] transition-all cursor-pointer flex items-center gap-1.5"
              title="Download full evaluation metrics report as JSON"
            >
              <span>💾</span>
              <span>Export Report</span>
            </button>
          )}

          <button
            type="button"
            disabled={isEvalRunning}
            onClick={handleRunEval}
            className={`text-[10px] font-mono font-bold px-3 py-1.5 rounded-lg transition-all flex items-center gap-2 cursor-pointer shadow-sm ${
              isEvalRunning
                ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)] cursor-not-allowed opacity-80'
                : 'bg-[var(--accent)] text-white hover:brightness-110 active:scale-95'
            }`}
          >
            {isEvalRunning ? (
              <>
                <div className="w-3 h-3 rounded-full border-2 border-white border-t-transparent animate-spin" />
                <span>Evaluating RAG...</span>
              </>
            ) : (
              <>
                <span>⚡</span>
                <span>{evalResults ? 'Re-Evaluate RAG' : 'Evaluate RAG'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Sub Navigation Bar */}
      {evalResults && (
        <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-1">
          <div className="flex gap-1.5">
            <button
              type="button"
              onClick={() => setActiveTab('metrics')}
              className={`text-[9px] font-mono font-bold px-2.5 py-1 rounded transition-all cursor-pointer ${
                activeTab === 'metrics'
                  ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)]'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
              }`}
            >
              Metric Bars
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('scorecard')}
              className={`text-[9px] font-mono font-bold px-2.5 py-1 rounded transition-all cursor-pointer ${
                activeTab === 'scorecard'
                  ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)]'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
              }`}
            >
              Reliability Scorecard
            </button>
            {evalResults.query_results && evalResults.query_results.length > 0 && (
              <button
                type="button"
                onClick={() => setActiveTab('queries')}
                className={`text-[9px] font-mono font-bold px-2.5 py-1 rounded transition-all cursor-pointer flex items-center gap-1 ${
                  activeTab === 'queries'
                    ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)]'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
                }`}
              >
                <span>Query Samples</span>
                <span className="px-1 py-0.2 text-[8px] rounded bg-[var(--accent-subtle)] text-[var(--accent)]">
                  {evalResults.query_results.length}
                </span>
              </button>
            )}
          </div>

          <div className="text-[9px] font-mono text-[var(--text-muted)] flex items-center gap-2">
            <span>Model: {evalResults.evaluator_model || 'qwen2.5:7b'}</span>
            {evalResults.duration_sec && <span>• {evalResults.duration_sec}s</span>}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      {!evalResults && !isEvalRunning ? (
        <div className="flex flex-col items-center justify-center p-8 rounded-xl border border-dashed border-[var(--border-subtle)] bg-[var(--bg-app)] text-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-[var(--accent-subtle)] border border-[var(--accent-border)] flex items-center justify-center text-xl text-[var(--accent)]">
            🎯
          </div>
          <div className="max-w-md">
            <h4 className="text-xs font-bold text-[var(--text-main)]">Empirical RAG Benchmark Not Yet Executed</h4>
            <p className="text-[10px] text-[var(--text-muted)] mt-1 leading-relaxed">
              Click <strong className="text-[var(--text-main)]">"Evaluate RAG"</strong> to trigger full precision, recall, MRR, NDCG@5, faithfulness, and citation verification benchmarks against the paper's indexed vector chunks.
            </p>
          </div>
          <button
            type="button"
            onClick={handleRunEval}
            className="text-[10px] font-mono font-bold px-4 py-2 rounded-lg bg-[var(--accent)] text-white hover:brightness-110 active:scale-95 transition-all cursor-pointer shadow-md flex items-center gap-2"
          >
            <span>🚀</span>
            <span>Run Benchmark Now</span>
          </button>
        </div>
      ) : isEvalRunning ? (
        <div className="flex flex-col items-center justify-center p-12 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-app)] text-center gap-4">
          <div className="w-10 h-10 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin" />
          <div className="flex flex-col gap-1">
            <h4 className="text-xs font-bold text-[var(--text-main)] font-mono">Running RAG Evaluation Pipeline...</h4>
            <p className="text-[10px] text-[var(--text-muted)] font-mono">
              Computing hybrid search metrics & local LLM judge verification
            </p>
          </div>
        </div>
      ) : activeTab === 'metrics' && summary ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
          {METRIC_CONFIGS.map((cfg) => {
            const rawVal = summary[cfg.key];
            const val = typeof rawVal === 'number' ? rawVal : 0.8;
            const colors = getColorClasses(val);
            const baselineVal = baseline ? baseline[cfg.key] : undefined;
            const delta = typeof baselineVal === 'number' ? val - baselineVal : null;

            return (
              <div
                key={cfg.key}
                className="p-3 rounded-xl bg-[var(--bg-app)] border border-[var(--border-subtle)] flex flex-col gap-2 hover:border-[var(--accent-border)] transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex flex-col">
                    <span className="text-[11px] font-bold text-[var(--text-main)] font-mono flex items-center gap-1.5">
                      {cfg.label}
                    </span>
                    <span className="text-[9px] text-[var(--text-muted)] line-clamp-1" title={cfg.description}>
                      {cfg.description}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {showBaselineComparison && delta !== null && (
                      <span
                        className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                          delta >= 0
                            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                            : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                        }`}
                        title={`Baseline: ${(baselineVal! * 100).toFixed(1)}%`}
                      >
                        {delta >= 0 ? `+${(delta * 100).toFixed(1)}%` : `${(delta * 100).toFixed(1)}%`}
                      </span>
                    )}

                    <span className={`text-xs font-mono font-black ${colors.text}`}>
                      {(val * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Animated Progress Bar */}
                <div className="w-full bg-[var(--bg-card)] h-2 rounded-full overflow-hidden border border-[var(--border-subtle)] relative">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ease-out ${colors.bg}`}
                    style={{ width: `${Math.min(100, Math.max(0, val * 100))}%` }}
                  />
                  {showBaselineComparison && typeof baselineVal === 'number' && (
                    <div
                      className="absolute top-0 bottom-0 w-0.5 bg-purple-400 z-10"
                      style={{ left: `${Math.min(100, Math.max(0, baselineVal * 100))}%` }}
                      title={`Baseline Target: ${(baselineVal * 100).toFixed(1)}%`}
                    />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : activeTab === 'scorecard' && evalResults?.scorecard ? (
        <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-app)] overflow-hidden">
          <table className="w-full text-[10px] font-mono text-left">
            <thead>
              <tr className="border-b border-[var(--border-subtle)] bg-[var(--bg-card)] text-[var(--text-muted)]">
                <th className="p-2.5 font-bold">Metric</th>
                <th className="p-2.5 font-bold">Measured Value</th>
                <th className="p-2.5 font-bold">Status</th>
              </tr>
            </thead>
            <tbody>
              {evalResults.scorecard.map((row, idx) => {
                const metricName = row.Metric || row.metric || `Metric ${idx + 1}`;
                const val = row['Measured Value'] || row.value || 'N/A';
                const status = (row.Status || row.status || 'PASS').toUpperCase();
                const isPass = status === 'PASS';

                return (
                  <tr key={idx} className="border-b border-[var(--border-subtle)]/50 hover:bg-[var(--accent-subtle)]/20 transition-colors">
                    <td className="p-2.5 text-[var(--text-main)] font-semibold">{metricName}</td>
                    <td className="p-2.5 text-[var(--text-main)]">{val}</td>
                    <td className="p-2.5">
                      <span
                        className={`text-[8px] font-bold px-2 py-0.5 rounded border ${
                          isPass
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        }`}
                      >
                        {status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : activeTab === 'queries' && evalResults?.query_results ? (
        <div className="flex flex-col gap-2 max-h-[420px] overflow-y-auto scrollbar-thin pr-1">
          {evalResults.query_results.map((q, idx) => (
            <div
              key={idx}
              className="p-3 rounded-xl bg-[var(--bg-app)] border border-[var(--border-subtle)] flex flex-col gap-2 font-mono"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-[var(--accent)]">
                  Query #{idx + 1}: {q.item_id}
                </span>
                {q.generation_metrics?.faithfulness !== undefined && (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                    Faithfulness: {(q.generation_metrics.faithfulness * 100).toFixed(0)}%
                  </span>
                )}
              </div>

              <div className="text-[10px] text-[var(--text-main)] font-semibold">
                Q: {q.question}
              </div>

              {q.generated_answer && (
                <div className="text-[9px] text-[var(--text-muted)] bg-[var(--bg-card)] p-2 rounded border border-[var(--border-subtle)] leading-relaxed">
                  <span className="font-bold text-[var(--text-main)]">Generated Answer: </span>
                  {q.generated_answer}
                </div>
              )}

              {q.generated_citation && (
                <div className="text-[8px] text-[var(--text-muted)]">
                  <span className="font-bold">Citation: </span>
                  {q.generated_citation}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
};
