import React, { useRef, useEffect } from 'react';
import { useLogsStore } from '../../../store/logsStore';
import { usePanelStore } from '../../../store/panelStore';
import { MilestoneTracker } from '../analysis/MilestoneTracker';
import { StatsCharts } from '../analysis/StatsCharts';
import { FaTerminal, FaMagnifyingGlass, FaCircleInfo, FaTriangleExclamation, FaCircleXmark, FaCheck } from 'react-icons/fa6';
import { FaTasks } from 'react-icons/fa';
import { IoClose } from 'react-icons/io5';

export const LogsDrawer: React.FC = () => {
  const [activeTab, setActiveTab] = React.useState<'logs' | 'process'>('logs');
  const { logs, filter, setFilter, searchQuery, setSearchQuery } = useLogsStore();
  const { isLogsOpen, toggleLogs, isAnalyzing } = usePanelStore();
  const consoleRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of logs on updates or drawer toggle
  useEffect(() => {
    if (consoleRef.current && activeTab === 'logs') {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [logs, isLogsOpen, activeTab]);

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
      className={`absolute left-0 right-0 bottom-0 h-[360px] bg-background/85 border-t border-border/55 shadow-[0_-10px_40px_rgba(0,0,0,0.2)] backdrop-blur-xl flex flex-col z-30 transform transition-all duration-400 cubic-bezier(0.4, 0, 0.2, 1) rounded-t-2xl select-none ${
        isLogsOpen 
          ? 'translate-y-0 opacity-100' 
          : 'translate-y-full opacity-0 pointer-events-none'
      }`}
      aria-label="System Logs Console"
    >
      {/* Header controls and Tab triggers inside drawer */}
      <div className="flex flex-col gap-2.5 px-5 py-3 border-b border-border/45 bg-background/50 shrink-0">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            {/* Tabs Selector */}
            <div className="flex items-center gap-1.5 p-0.5 bg-foreground/5 border border-border/20 rounded-lg">
              <button
                onClick={() => setActiveTab('logs')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider font-mono transition-all duration-300 cursor-pointer ${
                  activeTab === 'logs'
                    ? 'bg-card text-foreground border border-border/30 shadow-xs'
                    : 'text-foreground/45 hover:text-foreground hover:bg-foreground/5'
                }`}
              >
                <FaTerminal className="text-xs shrink-0" />
                Console Logs
                {isAnalyzing && (
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                )}
              </button>
              <button
                onClick={() => setActiveTab('process')}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider font-mono transition-all duration-300 cursor-pointer ${
                  activeTab === 'process'
                    ? 'bg-card text-foreground border border-border/30 shadow-xs'
                    : 'text-foreground/45 hover:text-foreground hover:bg-foreground/5'
                }`}
              >
                <FaTasks className="text-xs shrink-0" />
                Process Tracker
              </button>
            </div>
          </div>

          <button 
            onClick={toggleLogs}
            className="p-1.5 rounded-full text-foreground/50 hover:text-foreground hover:bg-foreground/10 transition-colors focus:outline-none focus:ring-2 focus:ring-brass/50 cursor-pointer"
            aria-label="Close Logs Panel"
          >
            <IoClose className="text-lg" />
          </button>
        </div>

        {/* Filter bar and search controls (Only visible under logs tab) */}
        {activeTab === 'logs' && (
          <div className="flex items-center justify-between gap-3 animate-fade-in">
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
        )}
      </div>

      {/* Terminal log rows container */}
      {activeTab === 'logs' && (
        <div 
          ref={consoleRef}
          className="flex-1 overflow-y-auto p-4 font-mono text-[10px] flex flex-col gap-1.5 bg-black/20 select-text scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent animate-fade-in"
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
      )}

      {/* Process tracker container (Milestone steps + charts) */}
      {activeTab === 'process' && (
        <div className="flex-1 overflow-y-auto p-5 flex flex-col md:flex-row gap-8 bg-black/15 scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent animate-fade-in select-none">
          {/* Milestone steps checklist */}
          <div className="flex-1 flex flex-col gap-3 min-w-[200px]">
            <span className="text-[9px] font-mono font-bold tracking-[0.2em] text-brass uppercase">
              {'//'} Pipeline Step Checklist
            </span>
            <MilestoneTracker />
          </div>

          {/* Stats charts */}
          <div className="w-full md:w-[280px] flex flex-col gap-3 shrink-0">
            <span className="text-[9px] font-mono font-bold tracking-[0.2em] text-brass uppercase">
              {'//'} Analytics Metric Depth
            </span>
            <StatsCharts />
          </div>
        </div>
      )}
    </aside>
  );
};
