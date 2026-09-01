import React, { useEffect, useRef } from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { DropZone } from '../../ui/DropZone';
import { FiFileText, FiPlus } from 'react-icons/fi';
import { MessageBubble } from './MessageBubble';

interface MessageFeedProps {
  isMaximized: boolean;
}

export const MessageFeed: React.FC<MessageFeedProps> = ({ isMaximized }) => {
  const { messages, isChatGenerating, selectedModel } = usePanelStore();

  return (
    <div className="flex-1 flex flex-col items-center w-full z-10 relative">
      <div className="max-w-[800px] w-full px-4 pt-6 pb-6 flex flex-col gap-6 flex-1 min-h-full">

        {/* ── 1. Welcome / Empty State ─────────────────────────────────── */}
        {messages.length === 0 && (
          <div className="flex-grow flex flex-col items-center justify-center text-center gap-4 max-w-[480px] mx-auto my-auto py-8 select-none animate-fade-in">
            <div className="w-12 h-12 rounded-2xl bg-[var(--accent-subtle)] border border-[var(--accent-border)] flex items-center justify-center shadow-lg shrink-0">
              <FiFileText className="text-[var(--accent)] text-2xl animate-pulse" />
            </div>
            <div className="flex flex-col gap-1">
              <h2 className="text-base font-bold tracking-tight text-[var(--text-main)]">
                Welcome to Synthexis
              </h2>
              <p className="text-[11px] text-[var(--text-muted)] font-mono tracking-wide leading-relaxed max-w-[400px]">
                To begin, click the{' '}
                {!isMaximized && <FiFileText className="inline text-xs mx-0.5 text-[var(--text-main)]" />}{' '}
                file or <FiPlus className="inline text-xs mx-0.5 text-[var(--text-main)]" /> button in the chatbox
                {isMaximized ? ', or drop files directly below.' : '.'}
              </p>
            </div>
            {isMaximized && (
              <div className="w-full border app-border rounded-2xl p-3 bg-[var(--bg-card)] backdrop-blur-sm mt-2">
                <DropZone />
              </div>
            )}
          </div>
        )}

        {/* ── 3. Chat Messages ──────────────────────────────────────────── */}
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            msg={msg}
          />
        ))}

        {/* ── 4. Live Model Processing & ReACT Thinking Loader ─────────── */}
        {isChatGenerating && (
          <div className="flex flex-col gap-3 max-w-[85%] self-start animate-fade-in my-2">
            <div className="flex items-center gap-2 text-xs font-mono text-[var(--accent)]">
              <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-ping" />
              <span className="font-semibold tracking-wide">Synthexis ReACT Agent is processing...</span>
              <span className="text-[10px] opacity-80 bg-[var(--accent-subtle)] text-[var(--accent)] px-2 py-0.5 rounded-md border border-[var(--accent-border)] font-mono">
                {selectedModel || 'llama-3.3-70b'}
              </span>
            </div>
            
            <div className="p-4 rounded-2xl bg-[var(--bg-card)] border app-border shadow-lg flex flex-col gap-3 text-xs">
              <div className="flex items-center gap-3 text-[var(--text-main)] font-mono">
                <div className="w-4 h-4 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin shrink-0" />
                <span className="animate-pulse">Retrieving paper RAG vector chunks & reasoning...</span>
              </div>
              <div className="pl-7 text-[11px] text-[var(--text-muted)] font-mono flex flex-col gap-1 border-l border-[var(--accent-border)] my-1">
                <span className="text-[var(--accent)]">THOUGHT: Searching indexed document sections & vector DB embeddings</span>
                <span className="opacity-80">ACTION: Querying PaperVectorDB hybrid cosine similarity</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};