import React, { useState } from 'react';
import { IconCopy, IconCheck } from '../components/ui/Icons';

// ─── Code Copy Button ─────────────────────────────────────────────────────────

export const CodeCopyButton: React.FC<{ code: string }> = ({ code }) => {
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
      className="flex items-center gap-1 text-[9px] font-mono text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors px-2 py-0.5 rounded hover:bg-[var(--accent-subtle)] cursor-pointer select-none"
      title="Copy code"
    >
      {copied ? (
        <>
          <IconCheck className="text-emerald-400 text-[10px]" />
          <span className="text-emerald-400 font-bold">COPIED</span>
        </>
      ) : (
        <>
          <IconCopy className="text-[10px]" />
          <span>COPY</span>
        </>
      )}
    </button>
  );
};

// ─── Inline Markdown Parser ───────────────────────────────────────────────────

export const parseInlineMarkdown = (text: string): React.ReactNode[] => {
  if (!text) return [];

  // Split by inline code: `code`
  const codeParts = text.split(/(`[^`]+`)/g);

  return codeParts.flatMap((codePart, cIdx) => {
    if (codePart.startsWith('`') && codePart.endsWith('`')) {
      return [
        <code
          key={`code-${cIdx}`}
          className="px-1.5 py-0.5 rounded bg-[var(--bg-base)]/80 border app-border font-mono text-[10.5px] text-[var(--accent)] mx-0.5 select-all"
        >
          {codePart.slice(1, -1)}
        </code>,
      ];
    }

    // Split by bold-italic: ***text***
    const boldItalicParts = codePart.split(/(\*\*\*[^*]+\*\*\*)/g);

    return boldItalicParts.flatMap((biPart, biIdx) => {
      if (biPart.startsWith('***') && biPart.endsWith('***')) {
        return [
          <strong key={`bi-${cIdx}-${biIdx}`} className="font-bold text-[var(--text-main)] italic">
            {biPart.slice(3, -3)}
          </strong>,
        ];
      }

      // Split by bold: **text**
      const boldParts = biPart.split(/(\*\*[^*]+\*\*)/g);

      return boldParts.flatMap((bPart, bIdx) => {
        if (bPart.startsWith('**') && bPart.endsWith('**')) {
          return [
            <strong key={`b-${cIdx}-${biIdx}-${bIdx}`} className="font-bold text-[var(--text-main)]">
              {bPart.slice(2, -2)}
            </strong>,
          ];
        }

        // Split by italic: *text* or _text_
        const italicParts = bPart.split(/(\*[^*]+\*|_[^_]+_)/g);

        return italicParts.flatMap((iPart, iIdx) => {
          if (
            (iPart.startsWith('*') && iPart.endsWith('*') && iPart.length > 2) ||
            (iPart.startsWith('_') && iPart.endsWith('_') && iPart.length > 2)
          ) {
            return [
              <em key={`i-${cIdx}-${biIdx}-${bIdx}-${iIdx}`} className="italic text-[var(--text-main)]/95 font-medium">
                {iPart.slice(1, -1)}
              </em>,
            ];
          }

          // Format arrow connectors: "→" or "->"
          const arrowParts = iPart.split(/(→|->)/g);
          return arrowParts.map((aPart, aIdx) => {
            if (aPart === '→' || aPart === '->') {
              return (
                <span
                  key={`arrow-${cIdx}-${biIdx}-${bIdx}-${iIdx}-${aIdx}`}
                  className="inline-flex items-center text-[var(--accent)] font-bold px-1 select-none"
                  title="Flow step"
                >
                  →
                </span>
              );
            }

            return aPart;
          });
        });
      });
    });
  });
};

// ─── Table Component ─────────────────────────────────────────────────────────

export interface TableData {
  headers: string[];
  alignments: ('left' | 'center' | 'right')[];
  rows: string[][];
}

export const MarkdownTable: React.FC<{ table: TableData }> = ({ table }) => {
  return (
    <div className="my-3 w-full max-w-full overflow-x-auto [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden rounded-xl border app-border bg-[var(--bg-base)]/40 shadow-xs select-text">
      <table className="w-full border-collapse text-left text-xs font-sans table-auto">
        <thead>
          <tr className="border-b app-border bg-[var(--bg-card)]/90 backdrop-blur-sm">
            {table.headers.map((header, idx) => (
              <th
                key={idx}
                className="px-3.5 py-2 font-mono text-[10.5px] font-bold tracking-wider text-[var(--accent)] uppercase select-none break-words"
                style={{ textAlign: table.alignments[idx] || 'left' }}
              >
                {parseInlineMarkdown(header)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y app-border/30">
          {table.rows.map((row, rIdx) => (
            <tr
              key={rIdx}
              className="hover:bg-[var(--accent-subtle)]/20 transition-colors odd:bg-transparent even:bg-[var(--bg-card)]/25"
            >
              {row.map((cell, cIdx) => (
                <td
                  key={cIdx}
                  className="px-3.5 py-2.5 text-[12px] text-[var(--text-main)] leading-relaxed align-top break-words"
                  style={{ textAlign: table.alignments[cIdx] || 'left' }}
                >
                  {parseInlineMarkdown(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ─── Block Markdown Formatter ─────────────────────────────────────────────────

export const formatMessageContent = (content: string): React.ReactNode => {
  if (!content) return null;

  // Pre-process: convert pseudo-code / copied prompts (e.g. code\nCOPY\n...) into clean code blocks
  const normalized = content
    .replace(/\r\n/g, '\n')
    .replace(
      /code\s*\n\s*COPY\s*\n([\s\S]*?Answer[^\n]*\n)/g,
      (_, codeBody) => `\`\`\`text\n${codeBody.trim()}\n\`\`\`\n`
    );

  // Split out fenced code blocks
  const parts = normalized.split(/(```[\s\S]*?```)/g);

  return parts.map((part, index) => {
    if (part.startsWith('```')) {
      const match = part.match(/```(\w*)\n([\s\S]*?)```/);
      const language = match ? match[1] : '';
      const code = match ? match[2] : part.slice(3, -3);
      const trimmedCode = code.trim();

      return (
        <div
          key={`code-block-${index}`}
          className="my-3 flex flex-col w-full max-w-full text-left rounded-xl overflow-hidden border app-border bg-[var(--bg-card)]/90 shadow-md"
        >
          <div className="flex justify-between items-center px-3 py-1.5 bg-[var(--bg-base)]/60 border-b app-border">
            <span className="text-[9px] font-mono text-[var(--accent)] font-bold uppercase tracking-widest">
              {language || 'code'}
            </span>
            <CodeCopyButton code={trimmedCode} />
          </div>
          <pre className="font-mono text-[11px] p-3 text-[var(--text-main)] whitespace-pre-wrap break-words break-all leading-relaxed select-text selection:bg-[var(--accent-subtle)] w-full max-w-full overflow-x-hidden [scrollbar-width:none]">
            <code>{trimmedCode}</code>
          </pre>
        </div>
      );
    }

    // Process regular text lines into structured blocks
    const lines = part.split('\n');
    const nodes: React.ReactNode[] = [];
    let lineIdx = 0;

    while (lineIdx < lines.length) {
      const line = lines[lineIdx];
      const trimmed = line.trim();

      // Skip empty lines
      if (!trimmed) {
        lineIdx++;
        continue;
      }

      // ── 1. Markdown Tables ──
      if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        const tableLines: string[] = [];
        while (lineIdx < lines.length) {
          const cur = lines[lineIdx].trim();
          if (cur.startsWith('|') && cur.endsWith('|')) {
            tableLines.push(cur);
            lineIdx++;
          } else if (
            cur === '' &&
            lineIdx + 1 < lines.length &&
            lines[lineIdx + 1].trim().startsWith('|') &&
            lines[lineIdx + 1].trim().endsWith('|')
          ) {
            lineIdx++;
          } else {
            break;
          }
        }

        if (tableLines.length >= 2) {
          const rawHeaders = tableLines[0].split('|').slice(1, -1);
          const headers = rawHeaders.map((h) => h.trim());

          let dataStart = 1;
          const alignments: ('left' | 'center' | 'right')[] = headers.map(() => 'left');

          if (tableLines[1].replace(/[\s|:-]/g, '').length === 0) {
            dataStart = 2;
            const sepCols = tableLines[1].split('|').slice(1, -1);
            sepCols.forEach((col, cIdx) => {
              const cTrim = col.trim();
              if (cTrim.startsWith(':') && cTrim.endsWith(':')) {
                alignments[cIdx] = 'center';
              } else if (cTrim.endsWith(':')) {
                alignments[cIdx] = 'right';
              } else {
                alignments[cIdx] = 'left';
              }
            });
          }

          const rows = tableLines.slice(dataStart).map((rowLine) => {
            const rawCells = rowLine.split('|').slice(1, -1);
            return rawCells.map((c) => c.trim());
          });

          nodes.push(
            <MarkdownTable
              key={`table-${index}-${lineIdx}`}
              table={{ headers, alignments, rows }}
            />
          );
          continue;
        }
      }

      // ── 2. Markdown Headings (###, ##, #) ──
      if (trimmed.startsWith('### ')) {
        nodes.push(
          <h4
            key={`h3-${index}-${lineIdx}`}
            className="text-[12.5px] font-bold text-[var(--accent)] mt-3 mb-1 font-mono tracking-tight"
          >
            {parseInlineMarkdown(trimmed.slice(4))}
          </h4>
        );
        lineIdx++;
        continue;
      }
      if (trimmed.startsWith('## ')) {
        nodes.push(
          <h3
            key={`h2-${index}-${lineIdx}`}
            className="text-[13.5px] font-extrabold text-[var(--text-main)] mt-3.5 mb-1.5 border-b app-border pb-1"
          >
            {parseInlineMarkdown(trimmed.slice(3))}
          </h3>
        );
        lineIdx++;
        continue;
      }
      if (trimmed.startsWith('# ')) {
        nodes.push(
          <h2
            key={`h1-${index}-${lineIdx}`}
            className="text-[15px] font-black text-[var(--accent)] mt-4 mb-2"
          >
            {parseInlineMarkdown(trimmed.slice(2))}
          </h2>
        );
        lineIdx++;
        continue;
      }

      // ── 3. Blockquotes (> text) ──
      if (trimmed.startsWith('> ') || trimmed === '>') {
        const quoteLines: string[] = [];
        while (lineIdx < lines.length) {
          const qLine = lines[lineIdx].trim();
          if (qLine.startsWith('> ') || qLine === '>') {
            quoteLines.push(qLine.slice(2).trim());
            lineIdx++;
          } else {
            break;
          }
        }
        nodes.push(
          <blockquote
            key={`quote-${index}-${lineIdx}`}
            className="my-2.5 pl-3 border-l-2 border-[var(--accent)] bg-[var(--accent-subtle)]/15 py-1.5 pr-3 rounded-r-lg text-[11.5px] text-[var(--text-main)] italic"
          >
            {quoteLines.map((ql, qIdx) => (
              <p key={qIdx} className="leading-relaxed my-0.5">
                {parseInlineMarkdown(ql)}
              </p>
            ))}
          </blockquote>
        );
        continue;
      }

      // ── 4. Unordered Lists (- item or * item) ──
      if (/^[-*]\s+/.test(trimmed)) {
        const listItems: string[] = [];
        while (lineIdx < lines.length) {
          const lLine = lines[lineIdx].trim();
          const match = lLine.match(/^[-*]\s+(.*)/);
          if (match) {
            listItems.push(match[1]);
            lineIdx++;
          } else {
            break;
          }
        }
        nodes.push(
          <ul
            key={`ul-${index}-${lineIdx}`}
            className="my-2 space-y-1 pl-4 list-disc marker:text-[var(--accent)] text-[12px] text-[var(--text-main)]"
          >
            {listItems.map((item, itemIdx) => (
              <li key={itemIdx} className="leading-relaxed">
                {parseInlineMarkdown(item)}
              </li>
            ))}
          </ul>
        );
        continue;
      }

      // ── 5. Ordered Lists (1. item) ──
      if (/^\d+\.\s+/.test(trimmed)) {
        const numItems: string[] = [];
        while (lineIdx < lines.length) {
          const nLine = lines[lineIdx].trim();
          const match = nLine.match(/^\d+\.\s+(.*)/);
          if (match) {
            numItems.push(match[1]);
            lineIdx++;
          } else {
            break;
          }
        }
        nodes.push(
          <ol
            key={`ol-${index}-${lineIdx}`}
            className="my-2 space-y-1 pl-4 list-decimal marker:text-[var(--accent)] marker:font-mono text-[12px] text-[var(--text-main)]"
          >
            {numItems.map((item, itemIdx) => (
              <li key={itemIdx} className="leading-relaxed">
                {parseInlineMarkdown(item)}
              </li>
            ))}
          </ol>
        );
        continue;
      }

      // ── 6. Horizontal Rules (--- or ***) ──
      if (/^[-*_]{3,}$/.test(trimmed)) {
        nodes.push(
          <hr key={`hr-${index}-${lineIdx}`} className="my-3 border-t app-border" />
        );
        lineIdx++;
        continue;
      }

      // ── 7. Standard Paragraph Text ──
      nodes.push(
        <p
          key={`p-${index}-${lineIdx}`}
          className="my-1.5 leading-relaxed text-[12px] text-[var(--text-main)]"
        >
          {parseInlineMarkdown(trimmed)}
        </p>
      );
      lineIdx++;
    }

    return <React.Fragment key={`text-block-${index}`}>{nodes}</React.Fragment>;
  });
};
