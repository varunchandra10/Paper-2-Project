import React from 'react';

// ─── Code Copy Button ─────────────────────────────────────────────────────────

import { useState } from 'react';
import { FiCopy, FiCheck } from 'react-icons/fi';

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

// ─── Inline Markdown Parser ───────────────────────────────────────────────────

export const parseInlineMarkdown = (text: string): React.ReactNode[] => {
  const codeParts = text.split(/(`[^`]+`)/g);
  return codeParts.flatMap((part, cIdx) => {
    if (part.startsWith('`') && part.endsWith('`')) {
      return [
        <code
          key={`code-${cIdx}`}
          className="px-1.5 py-0.5 rounded bg-muted/60 border border-border/30 font-mono text-[10px] text-brass mx-0.5 select-all"
        >
          {part.slice(1, -1)}
        </code>,
      ];
    }
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

// ─── Block Markdown Formatter ─────────────────────────────────────────────────

export const formatMessageContent = (content: string): React.ReactNode => {
  if (!content) return null;

  const parts = content.split(/(```[\s\S]*?```)/g);

  return parts.map((part, index) => {
    if (part.startsWith('```')) {
      const match = part.match(/```(\w*)\n([\s\S]*?)```/);
      const language = match ? match[1] : '';
      const code = match ? match[2] : part.slice(3, -3);
      const trimmedCode = code.trim();

      return (
        <div
          key={`code-block-${index}`}
          className="my-3 flex flex-col w-full text-left rounded-xl overflow-hidden border border-border/50 bg-card/90 shadow-md"
        >
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

    const lines = part.split('\n')
      .map(line => line.replace(/\r$/, ''))
      .filter(line => line.trim() !== '**');

    return (
      <div key={`text-block-${index}`} className="flex flex-col gap-1 w-full text-left">
        {lines.map((line, lIdx) => {
          const trimmed = line.trim();
          if (!trimmed) return <div key={`empty-${lIdx}`} className="h-1.5" />;

          if (trimmed === '---' || trimmed === '***') {
            return <hr key={`hr-${lIdx}`} className="my-2 border-border/40" />;
          }

          if (trimmed.startsWith('> ')) {
            return (
              <blockquote
                key={`quote-${lIdx}`}
                className="border-l-2 border-brass/60 pl-3 my-1 text-muted-foreground italic text-[11px]"
              >
                {parseInlineMarkdown(trimmed.slice(2))}
              </blockquote>
            );
          }

          if (trimmed.startsWith('### ')) {
            return (
              <h3 key={`h3-${lIdx}`} className="text-xs font-serif font-bold text-brass mt-3 mb-1 select-none">
                {trimmed.slice(4)}
              </h3>
            );
          }
          if (trimmed.startsWith('## ')) {
            return (
              <h2 key={`h2-${lIdx}`} className="text-xs font-serif font-extrabold text-foreground mt-3 mb-1.5 select-none">
                {trimmed.slice(3)}
              </h2>
            );
          }
          if (trimmed.startsWith('# ')) {
            return (
              <h1 key={`h1-${lIdx}`} className="text-sm font-serif font-black text-brass border-b border-border/20 pb-1 mt-4 mb-2 select-none">
                {trimmed.slice(2)}
              </h1>
            );
          }

          if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
            return (
              <ul key={`ul-${lIdx}`} className="list-disc list-inside pl-2 text-[13px] text-foreground/85 leading-relaxed my-0.5">
                <li className="marker:text-brass">{parseInlineMarkdown(trimmed.slice(2))}</li>
              </ul>
            );
          }

          const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
          if (numMatch) {
            return (
              <ol key={`ol-${lIdx}`} className="list-decimal list-inside pl-2 text-[13px] text-foreground/85 leading-relaxed my-0.5">
                <li className="marker:text-brass/80 font-sans">{parseInlineMarkdown(numMatch[2])}</li>
              </ol>
            );
          }

          return (
            <p key={`p-${lIdx}`} className="text-[13px] text-foreground/85 leading-relaxed my-0.5 font-sans">
              {parseInlineMarkdown(line)}
            </p>
          );
        })}
      </div>
    );
  });
};
