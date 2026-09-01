import React from 'react';
import { IconCpu } from '../../ui/Icons';
import { ReActStepsAccordion } from './ReActStepsAccordion';
import { parseReAct } from './parseReAct';
import { parseInlineMarkdown, formatMessageContent } from './messageFormatters';
import { PdfAttachmentCard } from '../../ui/PdfAttachmentCard';

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
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ msg }) => {
  const isUser = msg.role === 'user';
  const reactParsed = !isUser ? parseReAct(msg.content) : null;

  return (
    <div
      className={`flex flex-col gap-1 font-sans animate-fade-in ${
        isUser
          ? 'items-end self-end max-w-[78%]'
          : 'items-start self-start max-w-[92%] w-full'
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
        className={`relative px-4 py-3 text-xs leading-relaxed transition-all duration-200 select-text ${
          isUser
            ? 'rounded-2xl rounded-tr-xs bg-[var(--accent)] text-white shadow-md font-medium'
            : 'rounded-2xl rounded-tl-xs bg-[var(--bg-card)] border app-border text-[var(--text-main)] shadow-lg'
        }`}
      >
        {/* Model Pill Header (Assistant only) */}
        {!isUser && msg.model_used && (
          <div className="flex items-center justify-between gap-2 mb-2 pb-1.5 border-b app-border">
            <span className="text-[10px] font-mono font-bold tracking-tight text-[var(--text-main)] uppercase flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Synthexis Assistant
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
        <div className="whitespace-pre-wrap font-sans">
          {isUser
            ? parseInlineMarkdown(msg.content)
            : formatMessageContent(
                reactParsed?.hasReAct ? reactParsed.answer : msg.content
              )}
        </div>
      </div>
    </div>
  );
};
