import React from 'react';
import { FiCpu } from 'react-icons/fi';
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


// ─── Main Component ───────────────────────────────────────────────────────────

export const MessageBubble: React.FC<MessageBubbleProps> = ({ msg }) => {
  const isUser = msg.role === 'user';
  const reactParsed = !isUser ? parseReAct(msg.content) : null;

  return (
    <div
      className={`flex flex-col gap-1.5 font-sans animate-fade-in ${
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

      {/* ── Message Bubble — theme-aware via CSS vars ──────────────────── */}
      <div
        className={`px-5 py-3.5 text-[13px] leading-relaxed border transition-colors duration-200 ${
          isUser
            ? 'rounded-2xl rounded-tr-sm shadow-[0_3px_14px_rgba(0,0,0,0.22)]'
            : 'rounded-2xl rounded-tl-sm w-full shadow-[0_2px_12px_rgba(0,0,0,0.05)]'
        }`}
        style={
          isUser
            ? {
                backgroundColor: 'var(--bubble-user)',
                borderColor: 'var(--bubble-user-border)',
                color: 'var(--bubble-user-fg)',
              }
            : {
                backgroundColor: 'var(--bubble-assistant)',
                borderColor: 'var(--bubble-assistant-border)',
                color: 'var(--bubble-assistant-fg)',
              }
        }
      >
        {/* ── Claude-style PDF attachment card (only in user bubble) ───── */}
        {isUser && msg.attachment && (
          <div className="mb-3 flex justify-end">
            <PdfAttachmentCard
              filename={msg.attachment.filename}
              paperId={msg.attachment.paperId}
            />
          </div>
        )}

        {/* Model tag inside assistant bubble */}
        {!isUser && msg.model_used && (
          <div className="flex justify-end mb-2.5">
            <span
              className="inline-flex items-center gap-1 text-[9px] px-2 py-0.5 rounded-full font-mono border select-none"
              style={{
                backgroundColor: 'rgba(201,154,62,0.08)',
                borderColor: 'rgba(201,154,62,0.22)',
                color: 'var(--brass)',
              }}
            >
              <FiCpu className="text-[9px]" />
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
