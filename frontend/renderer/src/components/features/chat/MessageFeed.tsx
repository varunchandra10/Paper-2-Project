import React, { useEffect, useRef, useState } from 'react';
import { usePanelStore } from '../../../store/panelStore';
import { DropZone } from '../../ui/DropZone';
import { FiFileText, FiPlus, FiCopy, FiCheck, FiCpu, FiUser } from 'react-icons/fi';

interface MessageFeedProps {
  isMaximized: boolean;
}

// Copy button for code blocks
const CodeCopyButton: React.FC<{ code: string }> = ({ code }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback if clipboard API is unavailable
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1 text-[9px] font-mono text-muted-foreground hover:text-brass transition-colors px-2 py-0.5 rounded hover:bg-white/5 cursor-pointer"
      title="Copy code"
    >
      {copied ? (
        <>
          <FiCheck className="text-emerald-400 text-[10px]" />
          <span className="text-emerald-400">Copied</span>
        </>
      ) : (
        <>
          <FiCopy className="text-[10px]" />
          <span>Copy</span>
        </>
      )}
    </button>
  );
};

// Helper to format inline markdown (bold **text** and inline code `code`)
const parseInlineMarkdown = (text: string): React.ReactNode[] => {
  // Split by inline code: `code`
  const codeParts = text.split(/(`[^`]+`)/g);
  return codeParts.flatMap((part, cIdx) => {
    if (part.startsWith('`') && part.endsWith('`')) {
      return [
        <code key={`code-${cIdx}`} className="px-1.5 py-0.5 rounded bg-black/30 border border-white/5 font-mono text-[10px] text-brass mx-0.5 select-all">
          {part.slice(1, -1)}
        </code>
      ];
    }

    // Split by bold: **bold**
    const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
    return boldParts.map((bPart, bIdx) => {
      if (bPart.startsWith('**') && bPart.endsWith('**')) {
        return (
          <strong key={`bold-${cIdx}-${bIdx}`} className="font-extrabold text-foreground">
            {bPart.slice(2, -2)}
          </strong>
        );
      }
      return bPart;
    });
  });
};

// Main Markdown block parser for chat bubbles
const formatMessageContent = (content: string) => {
  if (!content) return null;

  // Split by code blocks
  const parts = content.split(/(```[\s\S]*?```)/g);

  return parts.map((part, index) => {
    // Code block
    if (part.startsWith('```')) {
      const match = part.match(/```(\w*)\n([\s\S]*?)```/);
      const language = match ? match[1] : '';
      const code = match ? match[2] : part.slice(3, -3);
      const trimmedCode = code.trim();

      return (
        <div key={`code-block-${index}`} className="my-3 flex flex-col w-full text-left rounded-xl overflow-hidden border border-border/50 bg-black/60 shadow-md">
          <div className="flex justify-between items-center px-3 py-1.5 bg-muted/40 border-b border-border/30">
            <span className="text-[9px] font-mono text-brass/80 font-bold uppercase tracking-widest">
              {language || 'code'}
            </span>
            <CodeCopyButton code={trimmedCode} />
          </div>
          <pre className="font-mono text-[11px] p-3.5 text-foreground/90 overflow-x-auto leading-relaxed select-text selection:bg-brass/35 w-full">
            <code>{trimmedCode}</code>
          </pre>
        </div>
      );
    }

    // Regular Markdown text processing
    const lines = part.split('\n');
    return (
      <div key={`text-block-${index}`} className="flex flex-col gap-1 w-full text-left">
        {lines.map((line, lIdx) => {
          const trimmed = line.trim();
          if (!trimmed && line === '') return <div key={`empty-${lIdx}`} className="h-1.5" />;

          // Horizontal rule
          if (trimmed === '---' || trimmed === '***') {
            return <hr key={`hr-${lIdx}`} className="my-2 border-border/40" />;
          }

          // Blockquote
          if (trimmed.startsWith('> ')) {
            return (
              <blockquote key={`quote-${lIdx}`} className="border-l-2 border-brass/60 pl-3 my-1 text-muted-foreground italic text-[11px]">
                {parseInlineMarkdown(trimmed.slice(2))}
              </blockquote>
            );
          }

          // Headers
          if (trimmed.startsWith('### ')) {
            return <h3 key={`h3-${lIdx}`} className="text-xs font-serif font-bold text-brass mt-3 mb-1 select-none">{trimmed.slice(4)}</h3>;
          }
          if (trimmed.startsWith('## ')) {
            return <h2 key={`h2-${lIdx}`} className="text-xs font-serif font-extrabold text-foreground mt-3 mb-1.5 select-none">{trimmed.slice(3)}</h2>;
          }
          if (trimmed.startsWith('# ')) {
            return <h1 key={`h1-${lIdx}`} className="text-sm font-serif font-black text-brass border-b border-border/20 pb-1 mt-4 mb-2 select-none">{trimmed.slice(2)}</h1>;
          }

          // Bullet lists (* or -)
          if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
            return (
              <ul key={`ul-${lIdx}`} className="list-disc list-inside pl-2 text-[11px] text-foreground/85 leading-relaxed my-0.5">
                <li className="marker:text-brass">{parseInlineMarkdown(trimmed.slice(2))}</li>
              </ul>
            );
          }

          // Numbered lists (e.g., 1. )
          const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
          if (numMatch) {
            return (
              <ol key={`ol-${lIdx}`} className="list-decimal list-inside pl-2 text-[11px] text-foreground/85 leading-relaxed my-0.5">
                <li className="marker:text-brass/80 font-sans">{parseInlineMarkdown(numMatch[2])}</li>
              </ol>
            );
          }

          // Regular paragraph
          return (
            <p key={`p-${lIdx}`} className="text-[11px] text-foreground/85 leading-relaxed my-0.5 font-sans">
              {parseInlineMarkdown(line)}
            </p>
          );
        })}
      </div>
    );
  });
};

export const MessageFeed: React.FC<MessageFeedProps> = ({ isMaximized }) => {
  const { uploadedFileName, isAnalyzing, reportContent, messages } = usePanelStore();
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of conversation feed on new messages
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, isAnalyzing, reportContent]);

  return (
    <div 
      ref={containerRef}
      className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-border/30 scrollbar-track-transparent z-10 relative flex flex-col items-center"
    >
      <div className="max-w-[800px] w-full px-4 py-6 flex flex-col gap-6 flex-1 min-h-full">
        
        {/* 1. Empty/Welcome state when no file is loaded */}
        {!uploadedFileName && messages.length === 0 && (
          <div className="flex-grow flex flex-col items-center justify-center text-center gap-4 max-w-[480px] mx-auto my-auto py-8 select-none animate-fade-in">
            <div className="w-12 h-12 rounded-2xl bg-brass/10 border border-brass/30 flex items-center justify-center shadow-lg shadow-brass/5 shrink-0">
              <FiFileText className="text-brass text-2xl animate-pulse" />
            </div>
            
            <div className="flex flex-col gap-1">
              <h2 className="text-base font-bold tracking-tight text-foreground">
                Welcome to Synthexis
              </h2>
              <p className="text-[11px] text-muted-foreground font-mono tracking-wide leading-relaxed max-w-[400px]">
                To begin, click the {!isMaximized && <FiFileText className="inline text-xs mx-0.5 text-foreground" />} file or <FiPlus className="inline text-xs mx-0.5 text-foreground" /> button in the chatbox{isMaximized ? ", or drop files directly below." : "."}
              </p>
            </div>

            {isMaximized && (
              <div className="w-full border border-border/40 rounded-2xl p-3 bg-card/20 backdrop-blur-sm mt-2">
                <DropZone />
              </div>
            )}
          </div>
        )}

        {/* 2. Conversational Q&A Messages */}
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div 
              key={msg.id}
              className={`flex flex-col gap-1.5 font-sans animate-fade-in ${
                isUser ? 'items-end self-end max-w-[85%]' : 'items-start self-start max-w-[92%] w-full'
              }`}
            >
              {/* Header Label */}
              <div className="text-[9px] font-mono uppercase tracking-widest px-1 flex items-center gap-1.5 select-none text-muted-foreground/70">
                {isUser ? (
                  <>
                    <FiUser className="text-[10px]" />
                    <span>User</span>
                  </>
                ) : (
                  <>
                    <span className="w-1.5 h-1.5 bg-brass rounded-full shadow-[0_0_6px_rgba(212,175,55,0.8)]" />
                    <span className="font-semibold text-brass/90">Assistant</span>
                    {msg.model_used && (
                      <span className="inline-flex items-center gap-1 text-[8px] px-1.5 py-0.2 rounded bg-muted/60 text-muted-foreground border border-border/40 normal-case">
                        <FiCpu className="text-[9px]" />
                        {msg.model_used}
                      </span>
                    )}
                  </>
                )}
              </div>

              {/* Message Bubble */}
              <div 
                className={`px-4 py-3 rounded-2xl shadow-sm leading-relaxed border transition-all ${
                  isUser
                    ? 'bg-brass text-slate-950 font-medium border-brass/80 rounded-tr-xs shadow-brass/10'
                    : 'bg-card/90 border-border/60 text-foreground rounded-tl-xs w-full shadow-black/20'
                }`}
              >
                <div className="whitespace-pre-wrap font-sans">
                  {isUser ? parseInlineMarkdown(msg.content) : formatMessageContent(msg.content)}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};