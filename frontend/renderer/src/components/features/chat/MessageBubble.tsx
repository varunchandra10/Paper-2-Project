import React, { useState } from 'react';
import { IconCpu, IconRotateCcw, IconCopy, IconCheck } from '../../ui/Icons';
import { ReActStepsAccordion } from './ReActStepsAccordion';
import { parseReAct } from './parseReAct';
import { parseInlineMarkdown, formatMessageContent } from './messageFormatters';
import { PdfAttachmentCard } from '../../ui/PdfAttachmentCard';
import { APP_BRANDING } from '../../../constants/branding';
import { usePanelStore } from '../../../store/panelStore';

// ─── Types ───────────────────────────────────────────────────────────────────

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  model_used?: string;
  attachment?: {
    filename: string;
    paperId: string;
  };
}

interface MessageBubbleProps {
  msg: ChatMessage;
  associatedPrompt?: string;
  isLast?: boolean;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ msg, associatedPrompt, isLast: _isLast }) => {
  const isUser = msg.role === 'user';
  const reactParsed = !isUser ? parseReAct(msg.content) : null;
  const { regenerateMessage, isChatGenerating, selectedModel } = usePanelStore();
  const [copied, setCopied] = useState(false);

  const isErrorMessage = !isUser && (
    msg.content.includes('⚠️') ||
    msg.content.includes('rate limit') ||
    msg.content.includes('Error generating response') ||
    msg.content.includes('HTTP 429')
  );

  const handleCopy = () => {
    const textToCopy = reactParsed?.hasReAct ? reactParsed.answer : msg.content;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRerun = () => {
    if (isChatGenerating) return;
    const promptToRun = isUser ? msg.content : associatedPrompt;
    regenerateMessage(promptToRun);
  };

  return (
    <div
      className={`group flex flex-col gap-1 font-sans animate-fade-in min-w-0 max-w-full ${
        isUser
          ? 'items-end self-end max-w-[78%]'
          : 'items-start self-start max-w-[92%] w-full min-w-0 overflow-x-hidden'
      }`}
    >
      {/* ── Assistant: ReACT reasoning trace accordion ──────────────────── */}
      {!isUser && reactParsed?.hasReAct && (
        <ReActStepsAccordion
          thought={reactParsed.thought}
          action={reactParsed.action}
          observation={reactParsed.observation}
        />
      )}

      {/* ── PDF attachment card — floats ABOVE the text bubble ── */}
      {isUser && msg.attachment && (
        <div className="flex justify-end w-full">
          <PdfAttachmentCard
            filename={msg.attachment.filename}
            paperId={msg.attachment.paperId}
          />
        </div>
      )}

      {/* ── Main Message Bubble ─────────────────────────────────────────── */}
      <div
        className={`relative px-4 py-3 text-xs leading-relaxed transition-all duration-200 select-text min-w-0 max-w-full break-words overflow-x-hidden ${
          isUser
            ? 'rounded-2xl rounded-tr-xs bg-[var(--accent)] text-white shadow-md font-medium'
            : isErrorMessage
            ? 'rounded-2xl rounded-tl-xs bg-[var(--bg-card)] border border-amber-500/40 text-[var(--text-main)] shadow-lg'
            : 'rounded-2xl rounded-tl-xs bg-[var(--bg-card)] border app-border text-[var(--text-main)] shadow-lg'
        }`}
      >
        {/* Model Pill Header (Assistant only) */}
        {!isUser && msg.model_used && (
          <div className="flex items-center justify-between gap-2 mb-2 pb-1.5 border-b app-border">
            <span className="text-[10px] font-mono font-bold tracking-tight text-[var(--text-main)] uppercase flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              {APP_BRANDING.ASSISTANT_NAME}
            </span>
            <span
              className="text-[9px] font-mono font-semibold px-2 py-0.5 rounded-md bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)] flex items-center gap-1 select-none"
              title={`Inference model: ${msg.model_used}`}
            >
              <IconCpu className="text-[9px]" />
              {msg.model_used}
            </span>
          </div>
        )}

        {/* Text content */}
        <div className={`font-sans leading-relaxed break-words min-w-0 max-w-full ${isUser ? 'whitespace-pre-wrap' : 'select-text'}`}>
          {isUser
            ? parseInlineMarkdown(msg.content)
            : formatMessageContent(
                reactParsed?.hasReAct ? reactParsed.answer : msg.content
              )}
        </div>

        {/* Prominent in-bubble Retry CTA on error or rate-limit */}
        {isErrorMessage && (
          <div className="mt-3 pt-2.5 border-t border-[var(--warning-border)] flex items-center justify-between gap-3 flex-wrap bg-[var(--warning-bg)] -mx-4 -mb-3 px-4 py-2.5 rounded-b-2xl">
            <span className="text-[11px] text-[var(--warning-fg)] font-mono font-bold flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[var(--warning-fg)] animate-ping" />
              Rate limit reached for this model
            </span>
            <button
              onClick={handleRerun}
              disabled={isChatGenerating}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-[var(--warning-btn-bg)] hover:brightness-110 active:scale-95 text-[var(--warning-btn-fg)] border border-[var(--warning-btn-border)] text-[11px] font-mono font-bold transition-all cursor-pointer shadow-xs disabled:opacity-50"
              title={`Retry prompt with ${selectedModel}`}
            >
              <IconRotateCcw className="text-xs text-[var(--warning-fg)]" />
              <span>Retry prompt ({selectedModel})</span>
            </button>
          </div>
        )}
      </div>

      {/* ── Action Toolbar below Bubble (ChatGPT & Claude style) ────────────────── */}
      <div className={`flex items-center gap-2 px-1 mt-1 select-none ${isUser ? 'justify-end' : 'justify-start'}`}>
        {/* Assistant Actions: Copy & Re-run */}
        {!isUser && (
          <div className="flex items-center gap-1.5 opacity-80 hover:opacity-100 transition-opacity">
            <button
              onClick={handleCopy}
              className="inline-flex items-center gap-1.5 px-2 py-1 rounded-lg text-[11px] text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] border border-transparent hover:border-[var(--border-color)] transition-all cursor-pointer"
              title="Copy answer to clipboard"
            >
              {copied ? <IconCheck className="text-xs text-emerald-400" /> : <IconCopy className="text-xs" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              onClick={handleRerun}
              disabled={isChatGenerating}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all cursor-pointer border disabled:opacity-40 active:scale-95 ${
                isErrorMessage
                  ? 'bg-[var(--warning-bg)] hover:brightness-110 border-[var(--warning-border)] text-[var(--warning-fg)] font-bold shadow-xs'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] border-transparent hover:border-[var(--border-color)]'
              }`}
              title={`Re-run this prompt with ${selectedModel}`}
            >
              <IconRotateCcw className={`text-xs ${isErrorMessage ? 'text-[var(--warning-fg)]' : 'text-[var(--accent)]'}`} />
              <span>{isErrorMessage ? 'Retry' : 'Re-run'}</span>
            </button>
          </div>
        )}

        {/* User Actions: Copy & Re-run Toolbar */}
        {isUser && (
          <div className="flex items-center gap-1.5 opacity-80 hover:opacity-100 transition-opacity">
            <button
              onClick={handleCopy}
              className="inline-flex items-center gap-1.5 px-2 py-1 rounded-lg text-[11px] text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] border border-transparent hover:border-[var(--border-color)] transition-all cursor-pointer"
              title="Copy prompt to clipboard"
            >
              {copied ? <IconCheck className="text-xs text-emerald-400" /> : <IconCopy className="text-xs" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              onClick={handleRerun}
              disabled={isChatGenerating}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-medium text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] border border-transparent hover:border-[var(--border-color)] transition-all cursor-pointer disabled:opacity-40 active:scale-95"
              title={`Re-run this prompt with ${selectedModel}`}
            >
              <IconRotateCcw className="text-xs text-[var(--accent)]" />
              <span>Re-run</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
