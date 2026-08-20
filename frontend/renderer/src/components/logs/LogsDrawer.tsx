import React, { useRef, useEffect } from 'react';
import { useLogsStore } from '../../store/logsStore';
import { usePanelStore } from '../../store/panelStore';
import { FaTerminal, FaMagnifyingGlass, FaCircleInfo, FaTriangleExclamation, FaCircleXmark, FaCheck } from 'react-icons/fa6';
import { IoClose } from 'react-icons/io5';

export const LogsDrawer: React.FC = () => {
  const { logs, filter, setFilter, searchQuery, setSearchQuery } = useLogsStore();
  const { isLogsOpen, toggleLogs } = usePanelStore();
  const consoleRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of logs on updates or drawer toggle
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [logs, isLogsOpen]);

  const filteredLogs = logs.filter((log) => {
    const matchesFilter = filter === 'all' || log.type === filter;
    const matchesSearch = log.text.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getLogIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <FaCheck className="text-confirmed text-[10px] shrink-0 mt-0.5" />;
      case 'warning':
        return <FaTriangleExclamation className="text-inferred text-[10px] shrink-0 mt-0.5" />;
      case 'error':
        return <FaCircleXmark className="text-error text-[10px] shrink-0 mt-0.5" />;
      case 'info':
        return <FaCircleInfo className="text-brass/80 text-[10px] shrink-0 mt-0.5" />;
      default:
        return <span className="text-foreground/30 font-bold select-none text-[10px] shrink-0">&gt;</span>;
    }
  };

  return (
    <aside 
      className={`absolute left-0 right-0 bottom-0 h-[300px] bg-background/80 border-t border-border/50 shadow-[0_-10px_40px_rgba(0,0,0,0.2)] backdrop-blur-xl flex flex-col z-10 transform transition-all duration-400 cubic-bezier(0.4, 0, 0.2, 1) rounded-t-2xl ${
        isLogsOpen 
          ? 'translate-y-0 opacity-100' 
          : 'translate-y-full opacity-0 pointer-events-none'
      }`}
      aria-label="System Logs Console"
    >
      {/* Header controls inside drawer */}
      <div className="flex flex-col gap-2.5 px-5 py-3.5 border-b border-border/40 bg-background/50">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-foreground/5 text-foreground/70">
              <FaTerminal className="text-sm" />
            </div>
            <span className="font-serif text-sm font-semibold text-foreground/90 tracking-wide flex items-center gap-2">
              Console Logs
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            </span>
          </div>

          <button 
            onClick={toggleLogs}
            className="p-1.5 rounded-full text-foreground/50 hover:text-foreground hover:bg-foreground/10 transition-colors focus:outline-none focus:ring-2 focus:ring-brass/50 cursor-pointer"
            aria-label="Close Logs Panel"
          >
            <IoClose className="text-lg" />
          </button>
        </div>

        {/* Filter bar and search controls */}
        <div className="flex items-center justify-between gap-3">
          {/* Search Input Field */}
          <div className="relative flex-1 max-w-[170px]">
            <FaMagnifyingGlass className="absolute left-2.5 top-1/2 -translate-y-1/2 text-foreground/30 text-[10px]" />
            <input 
              type="text"
              placeholder="Search logs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-background/70 border border-border/40 pl-7 pr-2 py-1 rounded-lg text-[10px] text-foreground placeholder-foreground/30 focus:outline-none focus:border-brass/50 focus:ring-1 focus:ring-brass/30 font-mono transition-all"
            />
          </div>

          {/* Level Filters Segmented Pills */}
          <div className="flex items-center gap-1 p-0.5 bg-foreground/5 border border-border/30 rounded-lg">
            {(['all', 'info', 'warning', 'error'] as const).map((lvl) => (
              <button
                key={lvl}
                onClick={() => setFilter(lvl)}
                className={`px-2 py-0.5 rounded-md text-[9px] font-mono capitalize transition-all duration-200 cursor-pointer ${
                  filter === lvl 
                    ? 'bg-brass text-ink font-bold shadow-xs' 
                    : 'text-muted-foreground hover:text-foreground hover:bg-foreground/5'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Terminal log rows container */}
      <div 
        ref={consoleRef}
        className="flex-1 overflow-y-auto p-4 font-mono text-[10px] flex flex-col gap-1.5 bg-black/20 select-text scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent"
      >
        {filteredLogs.map((log) => (
          <div 
            key={log.id} 
            className="flex items-start gap-2 py-1 px-2 rounded-md hover:bg-foreground/5 transition-colors group"
          >
            <span className="text-foreground/30 select-none font-light shrink-0">[{log.timestamp}]</span>
            {getLogIcon(log.type)}
            <span className={`flex-1 break-all leading-relaxed ${
              log.type === 'system' ? 'text-foreground/60 font-semibold' :
              log.type === 'success' ? 'text-confirmed font-medium' :
              log.type === 'warning' ? 'text-inferred font-medium' :
              log.type === 'error' ? 'text-error font-semibold' : 'text-foreground/90'
            }`}>
              {log.text}
            </span>
          </div>
        ))}
        
        {filteredLogs.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-foreground/30 py-8">
            <FaTerminal className="text-2xl opacity-40" />
            <span className="text-[11px] font-mono">No matching console logs.</span>
          </div>
        )}
      </div>
    </aside>
  );
};
