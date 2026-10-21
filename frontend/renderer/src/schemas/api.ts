/**
 * api.ts — Zod schemas for all backend API responses.
 *
 * Validates every JSON response at the network boundary so contract breaks
 * are caught immediately with a clear error, not buried in a silent fallback
 * chain like `data.content || data.response || data.raw_response`.
 *
 * Usage:
 *   import { parseChatStreamDone, parseUploadResponse } from '../../schemas/api';
 *   const meta = parseChatStreamDone(rawJson);   // throws ZodError on mismatch
 *   const safe = safeParseUpload(rawJson);        // returns { success, data?, error? }
 */

import { z } from 'zod';

// ---------------------------------------------------------------------------
// Shared primitives
// ---------------------------------------------------------------------------

/** Accepts any string, null, or undefined. */
const optStr = z.string().nullable().optional();
const reqStr = z.string();

// ---------------------------------------------------------------------------
// Chat schemas
// ---------------------------------------------------------------------------

/**
 * Metadata payload delivered in the SSE "done" event after streaming finishes.
 * Replaces the brittle `data.content || data.response || data.raw_response` chain.
 */
export const ChatStreamDoneSchema = z.object({
  conversation_id: reqStr,
  title: optStr,
  model_used: optStr,
  failover_model: optStr,
  thought: optStr,
  action: optStr,
  observation: optStr,
});
export type ChatStreamDone = z.infer<typeof ChatStreamDoneSchema>;

/**
 * Full non-streaming chat response (legacy /chat endpoint, still used as fallback).
 * `content` is the clean final answer; `answer` is the extracted ANSWER: block.
 */
export const ChatResponseSchema = z.object({
  conversation_id: reqStr,
  title: optStr,
  role: z.literal('assistant').default('assistant'),
  content: reqStr,
  answer: optStr,
  raw_response: optStr,
  model_used: optStr,
  failover_model: optStr,
  thought: optStr,
  action: optStr,
  observation: optStr,
});
export type ChatResponse = z.infer<typeof ChatResponseSchema>;

/**
 * Conversation list item returned by GET /conversations.
 */
export const ConversationItemSchema = z.object({
  conversation_id: reqStr.optional(),
  id: reqStr.optional(),
  title: reqStr.default('New Research Analysis'),
  project_id: z.string().nullable().optional(),
  created_at: z.union([z.string(), z.number()]).optional(),
  last_message: optStr,
  has_user_msg: z.boolean().optional(),
});
export type ConversationItem = z.infer<typeof ConversationItemSchema>;

export const ConversationsListSchema = z.object({
  conversations: z.array(ConversationItemSchema).default([]),
  active_conversation_id: z.string().nullable().optional(),
});

// ---------------------------------------------------------------------------
// Analysis / pipeline schemas
// ---------------------------------------------------------------------------

/**
 * Response from POST /history/upload — starts the ingestion pipeline.
 */
export const UploadResponseSchema = z.object({
  job_id: reqStr.optional(),
  paper_id: reqStr.optional(),
  conversation_id: reqStr.optional(),
  title: optStr,
  filename: optStr,
  duplicate: z.boolean().optional(),
  limits: z.record(z.string(), z.unknown()).optional(),
  status: optStr,
  message: optStr,
});
export type UploadResponse = z.infer<typeof UploadResponseSchema>;

/**
 * Message item within conversation history.
 */
export const ChatMessageItemSchema = z.object({
  id: optStr,
  message_id: optStr,
  role: z.string().default('user'),
  content: optStr,
  response: optStr,
  text: optStr,
  answer: optStr,
  model_used: optStr,
  model: optStr,
  paper_id: optStr,
  attachment: z.any().optional(),
});
export type ChatMessageItem = z.infer<typeof ChatMessageItemSchema>;

/**
 * Response from GET /conversations/{conversation_id}.
 */
export const ConversationDetailSchema = z.object({
  conversation_id: reqStr.optional(),
  id: reqStr.optional(),
  title: optStr,
  project_id: z.string().nullable().optional(),
  messages: z.array(ChatMessageItemSchema).default([]),
});
export type ConversationDetail = z.infer<typeof ConversationDetailSchema>;

/**
 * Response from POST /conversations.
 */
export const CreateConversationResponseSchema = z.object({
  conversation_id: reqStr,
  id: optStr,
  title: optStr,
  project_id: z.string().nullable().optional(),
});
export type CreateConversationResponse = z.infer<typeof CreateConversationResponseSchema>;

/**
 * Response from POST /history/{id}/generate_code and /trigger_analysis.
 * Only `job_id` is guaranteed — everything else is optional.
 */
export const JobStartResponseSchema = z.object({
  job_id: reqStr,
  paper_id: optStr,
  status: optStr,
  message: optStr,
});
export type JobStartResponse = z.infer<typeof JobStartResponseSchema>;

/**
 * Response from GET /extraction/status/{job_id}.
 */
export const ExtractionStatusSchema = z.object({
  job_id: optStr,
  status: optStr,
  report: optStr,
  progress: z.number().optional(),
  error: optStr,
});
export type ExtractionStatus = z.infer<typeof ExtractionStatusSchema>;

/**
 * Response from GET /papers/{id}/report.
 */
export const PaperReportSchema = z.object({
  report: optStr,
  paper_id: optStr,
  title: optStr,
});
export type PaperReport = z.infer<typeof PaperReportSchema>;

/**
 * SSE ERROR event payload: `{ "error": "...", "detail": "..." }`.
 */
export const SseErrorPayloadSchema = z.object({
  error: z.string().default('Unknown pipeline error'),
  detail: optStr,
});

// ---------------------------------------------------------------------------
// V2 Pipeline SSE event payload schemas
// ---------------------------------------------------------------------------

/**
 * Structured payload emitted for every V2 SSE event:
 * node_started, node_completed, refinement, retry, error,
 * pipeline_completed, pipeline_failed.
 *
 * Fields map directly to emit_event() in backend/app/core/events.py.
 */
export const V2PipelineEventSchema = z.object({
  event_id:  z.number().optional(),
  job_id:    optStr,
  paper_id:  optStr,
  event:     reqStr,
  node:      optStr,
  status:    optStr,
  progress:  z.number().optional(),
  timestamp: optStr,
  metadata:  z.record(z.string(), z.unknown()).optional(),
});
export type V2PipelineEvent = z.infer<typeof V2PipelineEventSchema>;

/**
 * Refinement metadata carried in the V2 refinement event.
 */
export const RefinementMetaSchema = z.object({
  reason:          optStr,
  adapted_fields:  z.record(z.string(), z.unknown()).optional(),
  attempt:         z.number().optional(),
  action:          optStr,
});
export type RefinementMeta = z.infer<typeof RefinementMetaSchema>;

/**
 * Retry (Reflexion repair) metadata carried in the V2 retry event.
 */
export const RetryMetaSchema = z.object({
  attempt:       z.number().optional(),
  max_retries:   z.number().optional(),
  error_summary: optStr,
  action:        optStr,
});
export type RetryMeta = z.infer<typeof RetryMetaSchema>;

// ---------------------------------------------------------------------------
// Safe parse helpers — log a warning but never crash the UI
// ---------------------------------------------------------------------------

/**
 * Parses with the given schema and returns the typed value.
 * On failure, logs the Zod error and returns the raw value cast to T
 * so the UI continues to function even if the backend contract drifts.
 */
export function safeParseFallback<T>(
  schema: z.ZodType<T>,
  raw: unknown,
  label: string
): T {
  const result = schema.safeParse(raw);
  if (!result.success) {
    console.warn(
      `[API Schema] "${label}" response did not match expected schema.\n`,
      result.error.format()
    );
    // Return raw cast — caller must handle possible undefined fields
    return raw as T;
  }
  return result.data;
}

// ---------------------------------------------------------------------------
// Run Manifest schemas (Phase 10 / Phase 22 Reproducibility)
// ---------------------------------------------------------------------------

export const PaperManifestInfoSchema = z.object({
  paper_id: reqStr,
  paper_hash: reqStr,
  paper_version: z.string().default('1.0.0'),
  file_name: optStr,
  file_size_bytes: z.number().nullable().optional(),
});
export type PaperManifestInfo = z.infer<typeof PaperManifestInfoSchema>;

export const ModelManifestConfigSchema = z.object({
  model: reqStr,
  model_version: z.string().default('qwen2.5:7b-instruct-q4_K_M'),
  provider: z.string().default('ollama'),
  temperature: z.number().default(0.0),
  top_p: z.number().default(0.9),
  max_output_tokens: z.number().default(8192),
  prompt_version: z.string().default('v2.0.0'),
});
export type ModelManifestConfig = z.infer<typeof ModelManifestConfigSchema>;

export const RetrievalManifestConfigSchema = z.object({
  embedding_model: z.string().default('nomic-embed-text'),
  embedding_version: z.string().default('2.0.0'),
  embedding_dimension: z.number().default(768),
  chunk_size: z.number().default(500),
  chunk_overlap: z.number().default(50),
  retrieval_strategy: z.string().default('hybrid_rrf'),
  top_k: z.number().default(5),
});
export type RetrievalManifestConfig = z.infer<typeof RetrievalManifestConfigSchema>;

export const SystemManifestConfigSchema = z.object({
  software_version: z.string().default('2.0.0'),
  manifest_schema_version: z.string().default('1.0.0'),
  os: reqStr,
  platform: reqStr,
  python_version: reqStr,
  torch_version: reqStr,
  git_commit: optStr,
});
export type SystemManifestConfig = z.infer<typeof SystemManifestConfigSchema>;

export const HardwareManifestConfigSchema = z.object({
  cpu: reqStr,
  cpu_cores: z.number().default(1),
  total_ram_gb: z.number().default(0),
  gpu_available: z.boolean().default(false),
  gpu_device: optStr,
  gpu_vram_total_gb: z.number().nullable().optional(),
});
export type HardwareManifestConfig = z.infer<typeof HardwareManifestConfigSchema>;

export const RunManifestSchema = z.object({
  run_id: reqStr,
  paper_id: reqStr,
  timestamp: optStr,
  paper: PaperManifestInfoSchema,
  model_info: ModelManifestConfigSchema.optional(),
  model_config: ModelManifestConfigSchema.optional(),
  retrieval_config: RetrievalManifestConfigSchema,
  system: SystemManifestConfigSchema,
  hardware: HardwareManifestConfigSchema,
  execution_summary: z.record(z.string(), z.any()).default({}),
});
export type RunManifest = z.infer<typeof RunManifestSchema>;

// Typed convenience wrappers used by slices
export const parseChatStreamDone       = (raw: unknown) => safeParseFallback(ChatStreamDoneSchema,            raw, 'ChatStreamDone');
export const parseChatResponse         = (raw: unknown) => safeParseFallback(ChatResponseSchema,              raw, 'ChatResponse');
export const parseConversationsList    = (raw: unknown) => safeParseFallback(ConversationsListSchema,         raw, 'ConversationsList');
export const parseConversationDetail   = (raw: unknown) => safeParseFallback(ConversationDetailSchema,        raw, 'ConversationDetail');
export const parseCreateConversation   = (raw: unknown) => safeParseFallback(CreateConversationResponseSchema, raw, 'CreateConversation');
export const parseUploadResponse       = (raw: unknown) => safeParseFallback(UploadResponseSchema,            raw, 'UploadResponse');
export const parseJobStart             = (raw: unknown) => safeParseFallback(JobStartResponseSchema,          raw, 'JobStartResponse');
export const parseExtractionStatus     = (raw: unknown) => safeParseFallback(ExtractionStatusSchema,          raw, 'ExtractionStatus');
export const parsePaperReport          = (raw: unknown) => safeParseFallback(PaperReportSchema,               raw, 'PaperReport');
export const parseSseError             = (raw: unknown) => safeParseFallback(SseErrorPayloadSchema,           raw, 'SseErrorPayload');
export const parseV2PipelineEvent      = (raw: unknown) => safeParseFallback(V2PipelineEventSchema,           raw, 'V2PipelineEvent');
export const parseRunManifest          = (raw: unknown) => safeParseFallback(RunManifestSchema,               raw, 'RunManifest');

