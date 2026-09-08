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

/** Accepts any string or coerces undefined/null to empty string. */
const optStr = z.string().optional();
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
