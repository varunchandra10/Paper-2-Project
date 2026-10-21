import React, { useState } from 'react';
import type { RunManifest } from '../../../schemas/api';
import {
  IconCheck,
  IconCopy,
  IconDownload,
  IconTerminal
} from '../../ui/Icons';

interface ManifestViewerProps {
  manifest: RunManifest | null;
  isLoading?: boolean;
}

export const ManifestViewer: React.FC<ManifestViewerProps> = ({ manifest, isLoading = false }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    paper: true,
    model: true,
    retrieval: true,
    system: true,
    hardware: true,
  });

  const toggleSection = (sectionKey: string) => {
    setOpenSections((prev) => ({
      ...prev,
      [sectionKey]: !prev[sectionKey],
    }));
  };

  if (isLoading) {
    return (
      <div className="p-3 bg-[var(--bg-base)] border app-border rounded-xl flex items-center justify-center gap-2 text-[10px] font-mono text-[var(--text-muted)]">
        <div className="w-3.5 h-3.5 rounded-full border border-[var(--accent)] border-t-transparent animate-spin" />
        <span>Loading Execution Run Manifest...</span>
      </div>
    );
  }

  if (!manifest) {
    return null;
  }

  const modelInfo = manifest.model_info || manifest.model_config || {
    model: 'default',
    provider: 'ollama',
    temperature: 0.0,
    top_p: 0.9,
    max_output_tokens: 8192,
    prompt_version: 'v2.0.0',
    model_version: '1.0.0'
  };

  // Check 18 reproducibility fields
  const isReproducible = Boolean(
    manifest.run_id &&
    manifest.paper?.paper_hash &&
    manifest.paper?.paper_id &&
    modelInfo.model &&
    modelInfo.provider &&
    modelInfo.prompt_version &&
    manifest.retrieval_config?.embedding_model &&
    manifest.retrieval_config?.retrieval_strategy &&
    manifest.system?.os &&
    manifest.system?.python_version &&
    manifest.system?.torch_version &&
    manifest.hardware?.cpu
  );

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(manifest, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadJson = () => {
    const filename = `${manifest.run_id || 'run'}_manifest.json`;
    const jsonStr = JSON.stringify(manifest, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-[var(--bg-base)] border app-border rounded-xl overflow-hidden font-mono text-[10px] select-none transition-all">
      {/* ── Main Collapsible Header Bar ──────────────────────────────── */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex flex-wrap items-center justify-between gap-2 p-3 bg-[var(--bg-card)]/80 hover:bg-[var(--bg-card)] cursor-pointer border-b app-border transition-all"
      >
        <div className="flex items-center gap-2">
          <IconTerminal className="text-xs text-[var(--accent)]" />
          <span className="font-bold text-[var(--text-main)] uppercase tracking-wider text-[9px]">
            Run Manifest
          </span>
          <span className="text-[var(--text-muted)]">
            run_id: <strong className="text-[var(--text-main)]">{manifest.run_id}</strong>
          </span>
          {manifest.paper?.paper_hash && (
            <span
              className="text-[8px] bg-[var(--bg-base)] px-1.5 py-0.2 rounded border app-border text-[var(--text-muted)] max-w-[130px] truncate"
              title={manifest.paper.paper_hash}
            >
              sha256:{manifest.paper.paper_hash.slice(0, 8)}...
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {isReproducible && (
            <span className="flex items-center gap-1 text-[8px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <IconCheck className="text-[9px]" />
              <span>Reproducible ✓</span>
            </span>
          )}

          <span className="text-[9px] text-[var(--text-muted)] font-bold">
            {isExpanded ? '▲ Collapse' : '▼ Expand'}
          </span>
        </div>
      </div>

      {/* ── Expanded Content Sections ───────────────────────────────── */}
      {isExpanded && (
        <div className="p-3.5 flex flex-col gap-3 bg-[var(--bg-base)] select-text">
          {/* Action Bar */}
          <div className="flex items-center justify-between border-b app-border pb-2.5">
            <div className="text-[9px] text-[var(--text-muted)]">
              Timestamp: {manifest.timestamp || 'N/A'}
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleCopyJson}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[var(--bg-card)] hover:bg-[var(--accent-subtle)] text-[var(--text-main)] border app-border transition-all cursor-pointer text-[9px] font-bold"
              >
                {copied ? <IconCheck className="text-xs text-emerald-400" /> : <IconCopy className="text-xs" />}
                <span>{copied ? 'Copied!' : 'Copy JSON'}</span>
              </button>

              <button
                type="button"
                onClick={handleDownloadJson}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[var(--accent)] hover:opacity-90 text-white transition-all cursor-pointer text-[9px] font-bold shadow-xs"
              >
                <IconDownload className="text-xs" />
                <span>Download JSON</span>
              </button>
            </div>
          </div>

          {/* Collapsible Sections Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {/* 1. Paper Section */}
            <div className="border app-border rounded-lg bg-[var(--bg-card)]/50 overflow-hidden">
              <div
                onClick={() => toggleSection('paper')}
                className="flex items-center justify-between p-2 bg-[var(--bg-card)] border-b app-border cursor-pointer"
              >
                <span className="font-bold text-amber-400 uppercase text-[9px]">
                  📄 Paper
                </span>
                <span className="text-[8px] text-[var(--text-muted)]">
                  {openSections.paper ? '▲' : '▼'}
                </span>
              </div>
              {openSections.paper && (
                <div className="p-2.5 flex flex-col gap-1 text-[9px] text-[var(--text-muted)]">
                  <div>paper_id: <strong className="text-[var(--text-main)]">{manifest.paper.paper_id}</strong></div>
                  <div className="break-all">hash: <strong className="text-[var(--text-main)]">{manifest.paper.paper_hash}</strong></div>
                  <div>version: <strong className="text-[var(--text-main)]">{manifest.paper.paper_version || '1.0.0'}</strong></div>
                  {manifest.paper.file_name && <div>filename: <strong className="text-[var(--text-main)]">{manifest.paper.file_name}</strong></div>}
                  {manifest.paper.file_size_bytes && <div>size: <strong className="text-[var(--text-main)]">{Math.round(manifest.paper.file_size_bytes / 1024)} KB</strong></div>}
                </div>
              )}
            </div>

            {/* 2. Model Section */}
            <div className="border app-border rounded-lg bg-[var(--bg-card)]/50 overflow-hidden">
              <div
                onClick={() => toggleSection('model')}
                className="flex items-center justify-between p-2 bg-[var(--bg-card)] border-b app-border cursor-pointer"
              >
                <span className="font-bold text-purple-400 uppercase text-[9px]">
                  🤖 Model & Prompt
                </span>
                <span className="text-[8px] text-[var(--text-muted)]">
                  {openSections.model ? '▲' : '▼'}
                </span>
              </div>
              {openSections.model && (
                <div className="p-2.5 flex flex-col gap-1 text-[9px] text-[var(--text-muted)]">
                  <div>model: <strong className="text-[var(--text-main)]">{modelInfo.model}</strong></div>
                  <div>provider: <strong className="text-[var(--text-main)]">{modelInfo.provider}</strong></div>
                  <div>temperature: <strong className="text-[var(--text-main)]">{modelInfo.temperature}</strong> | top_p: <strong className="text-[var(--text-main)]">{modelInfo.top_p}</strong></div>
                  <div>prompt_version: <strong className="text-[var(--text-main)]">{modelInfo.prompt_version}</strong></div>
                  <div>max_tokens: <strong className="text-[var(--text-main)]">{modelInfo.max_output_tokens}</strong></div>
                </div>
              )}
            </div>

            {/* 3. Retrieval Section */}
            <div className="border app-border rounded-lg bg-[var(--bg-card)]/50 overflow-hidden">
              <div
                onClick={() => toggleSection('retrieval')}
                className="flex items-center justify-between p-2 bg-[var(--bg-card)] border-b app-border cursor-pointer"
              >
                <span className="font-bold text-blue-400 uppercase text-[9px]">
                  🔍 Retrieval & RAG
                </span>
                <span className="text-[8px] text-[var(--text-muted)]">
                  {openSections.retrieval ? '▲' : '▼'}
                </span>
              </div>
              {openSections.retrieval && (
                <div className="p-2.5 flex flex-col gap-1 text-[9px] text-[var(--text-muted)]">
                  <div>embedding_model: <strong className="text-[var(--text-main)]">{manifest.retrieval_config.embedding_model}</strong> (dim: {manifest.retrieval_config.embedding_dimension})</div>
                  <div>strategy: <strong className="text-[var(--text-main)]">{manifest.retrieval_config.retrieval_strategy}</strong></div>
                  <div>chunk_size: <strong className="text-[var(--text-main)]">{manifest.retrieval_config.chunk_size}</strong> (overlap: {manifest.retrieval_config.chunk_overlap})</div>
                  <div>top_k: <strong className="text-[var(--text-main)]">{manifest.retrieval_config.top_k}</strong></div>
                </div>
              )}
            </div>

            {/* 4. System Section */}
            <div className="border app-border rounded-lg bg-[var(--bg-card)]/50 overflow-hidden">
              <div
                onClick={() => toggleSection('system')}
                className="flex items-center justify-between p-2 bg-[var(--bg-card)] border-b app-border cursor-pointer"
              >
                <span className="font-bold text-emerald-400 uppercase text-[9px]">
                  ⚙️ System & Runtime
                </span>
                <span className="text-[8px] text-[var(--text-muted)]">
                  {openSections.system ? '▲' : '▼'}
                </span>
              </div>
              {openSections.system && (
                <div className="p-2.5 flex flex-col gap-1 text-[9px] text-[var(--text-muted)]">
                  <div>os: <strong className="text-[var(--text-main)]">{manifest.system.os}</strong> ({manifest.system.platform})</div>
                  <div>software_version: <strong className="text-[var(--text-main)]">{manifest.system.software_version}</strong></div>
                  <div>python: <strong className="text-[var(--text-main)]">{manifest.system.python_version}</strong></div>
                  <div>torch: <strong className="text-[var(--text-main)]">{manifest.system.torch_version}</strong></div>
                  {manifest.system.git_commit && <div>git_commit: <strong className="text-[var(--text-main)]">{manifest.system.git_commit}</strong></div>}
                </div>
              )}
            </div>

            {/* 5. Hardware Section */}
            <div className="border app-border rounded-lg bg-[var(--bg-card)]/50 overflow-hidden md:col-span-2">
              <div
                onClick={() => toggleSection('hardware')}
                className="flex items-center justify-between p-2 bg-[var(--bg-card)] border-b app-border cursor-pointer"
              >
                <span className="font-bold text-pink-400 uppercase text-[9px]">
                  ⚡ Hardware Infrastructure
                </span>
                <span className="text-[8px] text-[var(--text-muted)]">
                  {openSections.hardware ? '▲' : '▼'}
                </span>
              </div>
              {openSections.hardware && (
                <div className="p-2.5 grid grid-cols-1 md:grid-cols-3 gap-2 text-[9px] text-[var(--text-muted)]">
                  <div>CPU: <strong className="text-[var(--text-main)]">{manifest.hardware.cpu}</strong> ({manifest.hardware.cpu_cores} cores)</div>
                  <div>RAM: <strong className="text-[var(--text-main)]">{manifest.hardware.total_ram_gb} GB</strong></div>
                  <div>GPU: <strong className="text-[var(--text-main)]">{manifest.hardware.gpu_available ? (manifest.hardware.gpu_device || 'CUDA Active') : 'CPU Only'}</strong> {manifest.hardware.gpu_vram_total_gb ? `(${manifest.hardware.gpu_vram_total_gb} GB VRAM)` : ''}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
