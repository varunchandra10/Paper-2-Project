/**
 * Centralized Model Constants & Catalog Fallbacks
 *
 * Single source of truth for selectable frontend conversational models,
 * fallback options, and backend-exclusion filters.
 */

export interface ModelOption {
  id: string;
  name: string;
  provider: 'Groq' | 'OpenRouter' | 'Ollama' | string;
  is_local?: boolean;
  description?: string;
}

/**
 * Fallback models for Groq (High-speed LPU inference)
 */
export const FALLBACK_GROQ: ModelOption[] = [
  { id: 'qwen/qwen3.8-27b', name: 'Qwen 3.8 27B', provider: 'Groq' },
  { id: 'openai/gpt-oss-120b', name: 'GPT-OSS 120B', provider: 'Groq' }
];

/**
 * Fallback models for OpenRouter (Free-tier community models)
 */
export const FALLBACK_OPENROUTER: ModelOption[] = [
  { id: 'google/gemini-2.5-flash', name: 'Gemini 2.5 Flash', provider: 'OpenRouter' },
  { id: 'deepseek/deepseek-r1:free', name: 'DeepSeek R1 (Free)', provider: 'OpenRouter' }
];

/**
 * Default selected model on initial launch
 */
export const DEFAULT_SELECTED_MODEL = 'qwen/qwen3.8-27b';

/**
 * Filter to exclude embedding models and backend-dedicated Dual Code Engine models
 * (e.g. Qwen 2.5 Coder 32B and Gemini 3.6 Flash are reserved for code synthesis)
 */
export const isExcludedModel = (m: { id?: string; name?: string }): boolean => {
  const id = (m?.id || '').toLowerCase();
  const name = (m?.name || '').toLowerCase();

  return (
    id.includes('embed') ||
    name.includes('embed') ||
    id.includes('qwen2.5-coder-32b') ||
    id.includes('qwen-2.5-coder-32b') ||
    id.includes('gemini-3.6')
  );
};

/**
 * Resolves the corresponding frontend model ID if a model_used string
 * indicates that an automatic failover or fallback occurred in the backend.
 * Returns null if no failover occurred, ensuring the user's manual selection is preserved.
 */
export const resolveFailoverModelId = (modelUsed?: string | null): string | null => {
  if (!modelUsed) return null;
  const lower = modelUsed.toLowerCase();

  // Only act when an automatic failover or fallback occurred
  const isFailover = lower.includes('failover') || lower.includes('fallback');
  if (!isFailover) return null;

  // 1. Google Gemini (e.g., "Gemini 2.0 Flash (Auto-Failover)" or "OpenRouter (google/gemini-2.5-flash Auto-Failover)")
  if (lower.includes('gemini')) {
    return 'google/gemini-2.5-flash';
  }

  // 2. DeepSeek R1 (e.g., "OpenRouter (deepseek/deepseek-r1:free Auto-Failover)")
  if (lower.includes('deepseek')) {
    return 'deepseek/deepseek-r1:free';
  }

  // 3. GPT-OSS (e.g., "Groq Cloud (openai/gpt-oss-120b Fallback)")
  if (lower.includes('gpt-oss')) {
    return 'openai/gpt-oss-120b';
  }

  // 4. Qwen / Groq Cloud Fallback (e.g., "Groq Cloud (qwen/qwen3.8-27b Fallback)")
  if (lower.includes('qwen') || lower.includes('groq')) {
    return 'qwen/qwen3.8-27b';
  }

  // Default resilient cloud failover
  return 'google/gemini-2.5-flash';
};

