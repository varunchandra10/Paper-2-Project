/**
 * Centralized API Configuration & Dynamic URL Resolution
 * 
 * Dynamically resolves the backend API Base URL based on runtime environment:
 * - In Electron or file:// protocol: points directly to http://localhost:8000
 * - In standard Vite browser development: uses '/api' proxy or VITE_BACKEND_URL if specified
 */

export const isElectronEnvironment = (): boolean => {
  return typeof window !== 'undefined' && (!!window.mascotAPI || window.location.protocol === 'file:');
};

export const getApiBase = (): string => {
  // Check for environment variable override (e.g. from .env or Vite config)
  const envUrl = typeof import.meta !== 'undefined' && import.meta.env?.VITE_BACKEND_URL;
  if (envUrl) {
    const cleanUrl = envUrl.replace(/\/+$/, '');
    return cleanUrl.endsWith('/api/v1') ? cleanUrl : `${cleanUrl}/api/v1`;
  }

  // Both Electron desktop window and browser dev hit the v1 API root
  return 'http://localhost:8000/api/v1';
};

/**
 * Singleton API Base URL string (always points to /api/v1)
 */
export const API_BASE = getApiBase();

/**
 * Standard API Endpoint Paths (V2 Architecture)
 */
export const API_ENDPOINTS = {
  // Models & Inference
  MODELS: `${API_BASE}/models`,
  LIMITS: `${API_BASE}/models/limits`,
  DUAL_ENGINE: `${API_BASE}/models/dual-engine`,
  MODELS_STATUS: `${API_BASE}/models/status`,

  // Papers (V2)
  PAPERS: `${API_BASE}/papers`,
  PAPER_UPLOAD: `${API_BASE}/papers/upload`,
  PAPER_UPLOAD_ALT: `${API_BASE}/history/upload`, // legacy alias
  PAPERS_RAG_QUERY: `${API_BASE}/papers/query`,

  // Pipeline Execution (V2)
  PIPELINE_ANALYZE: `${API_BASE}/pipeline/analyze`,
  PIPELINE_INGEST: `${API_BASE}/pipeline/analyze`, // legacy alias alias
  PIPELINE_JOB_STATUS: (jobId: string) => `${API_BASE}/pipeline/jobs/${jobId}`,
  PIPELINE_JOB_EVENTS: (jobId: string) => `${API_BASE}/pipeline/jobs/${jobId}/events`,
  PIPELINE_JOB_MANIFEST: (jobId: string) => `${API_BASE}/pipeline/jobs/${jobId}/manifest`,
  PIPELINE_MANIFESTS: `${API_BASE}/pipeline/manifests`,

  // Conversations & Chat
  CONVERSATIONS: `${API_BASE}/conversations`,
  CHAT_CONVERSATIONS: `${API_BASE}/chat/conversations`,
  CONVERSATIONS_ACTIVE: `${API_BASE}/conversations/active`,

  // Hardware & Monitoring
  HARDWARE: `${API_BASE}/hardware/metrics`,

  // User Profile & Onboarding
  USER_PROFILE: `${API_BASE}/user/profile`,
  AUTH_SETUP_WIZARD: `${API_BASE}/auth/setup-wizard`,
  AUTH_VERIFY_KEY: `${API_BASE}/auth/verify-key`,
  AUTH_CHECK_OLLAMA: `${API_BASE}/auth/check-ollama`,

  // Telemetry & Evals
  TELEMETRY: `${API_BASE}/telemetry/traces`,
  EVALS_BENCHMARK: (paperId: string) => `${API_BASE}/evals/benchmark/${paperId}`,
  EVALS_RUN_RAG: `${API_BASE}/evals/run-rag`,
  EVALS_BASELINE: `${API_BASE}/evals/baseline`,
} as const;

/**
 * Returns the V2 SSE pipeline event stream URL for a given job ID.
 * Backend supports /pipeline/jobs/{id}/events, /pipeline/stream/{id}, and /extraction/stream/{id}.
 */
export const getPipelineEventsUrl = (jobId: string): string =>
  `${API_BASE}/pipeline/jobs/${jobId}/events`;

/**
 * Returns the V2 job status URL for a given job ID.
 */
export const getPipelineJobUrl = (jobId: string): string =>
  `${API_BASE}/pipeline/jobs/${jobId}`;

/**
 * Returns the V2 run manifest URL for a given job ID.
 */
export const getPipelineManifestUrl = (jobId: string): string =>
  `${API_BASE}/pipeline/jobs/${jobId}/manifest`;

/**
 * Returns the V2 paper document URL for a given paper ID.
 */
export const getPaperUrl = (paperId: string): string =>
  `${API_BASE}/papers/${paperId}`;

/**
 * Returns the paper upload endpoint URL.
 */
export const getPaperUploadUrl = (): string =>
  `${API_BASE}/papers/upload`;

/**
 * Returns the V2 paper task sequence checklist URL.
 */
export const getPaperTaskUrl = (paperId: string): string =>
  `${API_BASE}/papers/${paperId}/task`;

/**
 * Returns the V2 paper verification walkthrough URL.
 */
export const getPaperWalkthroughUrl = (paperId: string): string =>
  `${API_BASE}/papers/${paperId}/walkthrough`;

/**
 * Returns the V2 paper knowledge graph URL.
 */
export const getPaperKnowledgeGraphUrl = (paperId: string): string =>
  `${API_BASE}/papers/${paperId}/knowledge_graph`;

/**
 * Returns the paper execution traces telemetry URL.
 */
export const getPaperTracesUrl = (paperId: string): string =>
  `${API_BASE}/papers/${paperId}/traces`;
