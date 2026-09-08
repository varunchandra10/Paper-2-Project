import React from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { MessageBubble } from './MessageBubble';
import { MessageSkeleton } from '../../ui/MessageSkeleton';
import { APP_BRANDING } from '../../../constants/branding';
import { RuexisLogo } from '../../ui/RuexisLogo';

interface MessageFeedProps {
  isMaximized: boolean;
}

const LIFECYCLE_STAGES = [
  { name: 'Research', color: '#6366f1' },
  { name: 'Understand', color: '#06b6d4' },
  { name: 'Extract', color: '#10b981' },
  { name: 'Examine', color: '#f59e0b' },
  { name: 'Implement', color: '#ef4444' },
  { name: 'Synthesize', color: '#a855f7' },
];

export const MessageFeed: React.FC<MessageFeedProps> = ({ isMaximized }) => {
  const { 
    messages, 
    isChatGenerating, 
    isMessagesLoading, 
    selectedModel, 
    uploadedFileName,
    streamingStatus,
    streamingThought,
    streamingAction
  } = usePanelStore();

  const filteredMessages = messages.filter(
    (msg) => msg.id !== 'welcome-rag-prompt' && !(typeof msg.content === 'string' && msg.content.includes('successfully ingested and indexed'))
  );

  return (
    <div className="flex-1 flex flex-col items-center w-full z-10 relative">
      <div className="max-w-[800px] w-full px-4 pt-6 pb-6 flex flex-col gap-6 flex-1 min-h-full">

        {/* ── 0. Conversation Switch Skeleton Loading State ────────────── */}
        {isMessagesLoading && <MessageSkeleton />}

        {/* ── 1. Welcome / Empty State ─────────────────────────────────── */}
        {!isMessagesLoading && messages.length === 0 && !uploadedFileName && (
          <div className={`flex-grow flex flex-col items-center justify-center text-center gap-4.5 mx-auto my-auto py-8 select-none animate-fade-in ${isMaximized ? 'max-w-[700px]' : 'max-w-[380px]'}`}>
            
            {/* Clockwise Rotating Life Cycle Logo */}
            <div 
              className="relative flex items-center justify-center select-none py-2 cursor-pointer group"
              title="REUXIS AI — Research Life Cycle Emblem"
            >
              <style>{`
                @keyframes rotate-clockwise {
                  0% { transform: rotate(0deg); }
                  100% { transform: rotate(360deg); }
                }
              `}</style>
              <div className="absolute w-28 h-28 rounded-full bg-[var(--accent)]/10 blur-xl pointer-events-none group-hover:bg-[var(--accent)]/20 transition-colors" />
              <div 
                className="inline-flex items-center justify-center animate-rotate-clockwise"
                style={{
                  animation: 'rotate-clockwise 14s linear infinite',
                  transformOrigin: '50% 50%',
                  willChange: 'transform'
                }}
              >
                <RuexisLogo size={76} showBackground={false} scaleFactor={1.22} />
              </div>
            </div>

            {/* Name of Project */}
            <div className="flex flex-col items-center gap-1.5">
              <h1 className="text-xl md:text-2xl font-bold tracking-tight text-[var(--text-main)] font-heading">
                {APP_BRANDING.NAME}
              </h1>
            </div>

            {/* All the Lifecycle Words: 3 in a row for minimized, 6 in single row for maximized */}
            <div className={
              isMaximized 
                ? "grid grid-cols-6 gap-2 w-full max-w-[660px] pt-1" 
                : "grid grid-cols-3 gap-2 w-full max-w-[340px] pt-1"
            }>
              {LIFECYCLE_STAGES.map((stage) => (
                <div 
                  key={stage.name}
                  className="flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-[var(--bg-card)] border app-border shadow-xs hover:border-[var(--accent-border)] hover:scale-105 transition-all duration-200 select-none"
                >
                  <span 
                    className="w-1.5 h-1.5 rounded-full shrink-0 animate-pulse" 
                    style={{ backgroundColor: stage.color }}
                  />
                  <span className="text-[11px] font-mono font-semibold tracking-wide text-[var(--text-main)] truncate">
                    {stage.name}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── 3. Chat Messages ──────────────────────────────────────────── */}
        {!isMessagesLoading && filteredMessages.map((msg, idx) => {
          // If this assistant message is empty while generating, don't show an empty card yet (the loader below is active)
          if (msg.role === 'assistant' && !msg.content.trim() && isChatGenerating) {
            return null;
          }
          let associatedPrompt: string | undefined;
          if (msg.role === 'assistant') {
            for (let i = idx - 1; i >= 0; i--) {
              if (filteredMessages[i].role === 'user') {
                associatedPrompt = filteredMessages[i].content;
                break;
              }
            }
          }
          return (
            <MessageBubble
              key={msg.id}
              msg={msg}
              associatedPrompt={associatedPrompt}
              isLast={idx === filteredMessages.length - 1}
            />
          );
        })}

        {/* ── 4. Live Model Processing & ReACT Thinking Loader ─────────── */}
        {isChatGenerating && (
          <div className="flex flex-col gap-3 max-w-[85%] self-start animate-fade-in my-2">
            <div className="flex items-center gap-2 text-xs font-mono text-[var(--accent)]">
              <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-ping" />
              <span className="font-semibold tracking-wide">{APP_BRANDING.AGENT_NAME} is processing...</span>
              <span className="text-[10px] opacity-80 bg-[var(--accent-subtle)] text-[var(--accent)] px-2 py-0.5 rounded-md border border-[var(--accent-border)] font-mono">
                {selectedModel || 'llama-3.3-70b'}
              </span>
            </div>
            
            <div className="p-4 rounded-2xl bg-[var(--bg-card)] border app-border shadow-lg flex flex-col gap-3 text-xs">
              <div className="flex items-center gap-3 text-[var(--text-main)] font-mono">
                <div className="w-4 h-4 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin shrink-0" />
                <span className="animate-pulse">{streamingStatus || 'Retrieving paper RAG vector chunks & reasoning...'}</span>
              </div>
              <div className="pl-7 text-[11px] text-[var(--text-muted)] font-mono flex flex-col gap-1 border-l border-[var(--accent-border)] my-1">
                <span className="text-[var(--accent)] line-clamp-3">THOUGHT: {streamingThought || 'Searching indexed document sections & vector DB embeddings'}</span>
                <span className="opacity-80 line-clamp-2">ACTION: {streamingAction || 'Querying PaperVectorDB hybrid cosine similarity'}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};