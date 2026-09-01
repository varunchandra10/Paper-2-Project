import React, { useRef, useEffect } from 'react';
import { useLogsStore } from '../../../store/logsStore';
import { usePanelStore } from '../../../store/panelStore';
import { MilestoneTracker } from '../analysis/MilestoneTracker';
import { StatsCharts } from '../analysis/StatsCharts';
import { 
  FaTerminal, 
  FaMagnifyingGlass, 
  FaCircleInfo, 
  FaTriangleExclamation, 
  FaCircleXmark, 
  FaCheck 
} from 'react-icons/fa6';
import { FaTasks } from 'react-icons/fa';
import { IoClose } from 'react-icons/io5';
import { FiTrash2 } from 'react-icons/fi';

export const LogsDrawer: React.FC = () => {
  const [activeTab, setActiveTab] = React.useState<'logs' | 'traces' | 'process'>('logs');
  const [traces, setTraces] = React.useState<any[]>([]);
  const { logs, filter, setFilter, searchQuery, setSearchQuery, clearLogs } = useLogsStore();
  const { isLogsOpen, toggleLogs, isAnalyzing, activePaperId } = usePanelStore();
  const consoleRef = useRef<HTMLDivElement>(null);

  // Poll execution traces when drawer is open and activePaperId is present
  useEffect(() => {
    if (isLogsOpen && activePaperId) {
      const fetchTraces = async () => {
        try {
          const apiBase = (typeof window !== 'undefined' && (!!window.mascotAPI || window.location.protocol === 'file:'))
            ? 'http://localhost:8000'
            : '/api';
          const resp = await fetch(`${apiBase}/history/${activePaperId}/traces`);
          if (resp.ok) {
            const data = await resp.json();
            setTraces(data.traces || []);
          }
        } catch (e) {
          // Silent fallback
        }
      };
      fetchTraces();
      const interval = setInterval(fetchTraces, 3000);
      return () => clearInterval(interval);
    }
  }, [isLogsOpen, activePaperId]);

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
        return <FaCheck className="text-emerald-400 text-[10px] shrink-0 mt-0.5" />;
      case 'warning':
        return <FaTriangleExclamation className="text-amber-400 text-[10px] shrink-0 mt-0.5" />;
      case 'error':
        return <FaCircleXmark className="text-red-400 text-[10px] shrink-0 mt-0.5" />;
      case 'info':
        return <FaCircleInfo className="text-brass text-[10px] shrink-0 mt-0.5" />;
      default:
        return <span className="text-muted-foreground/40 font-bold select-none text-[10px] shrink-0">&gt;</span>;
    }
  };

  const getLogCount = (type: string) => {
    if (type === 'all') return logs.length;
    return logs.filter((l) => l.type === type).length;
  };

  return (
    <aside 
      className={`absolute left-0 right-0 bottom-0 h-[380px] bg-card/95 border-t border-border/60 shadow-[0_-12px_40px_rgba(0,0,0,0.4)] backdrop-blur-2xl flex flex-col z-30 transform transition-all duration-300 ease-in-out rounded-t-2xl select-none ${
        isLogsOpen 
          ? 'translate-y-0 opacity-100' 
          : 'translate-y-full opacity-0 pointer-events-none'
      }`}
      aria-label="System Logs Console"
    >
      {/* ── Header Controls & Tab Triggers ────────────────────────── */}
      <div className="flex flex-col gap-2.5 px-4 py-3 border-b border-border/40 bg-muted/20 shrink-0">
        <div className="flex justify-between items-center">
          
          {/* Main Navigation Tabs */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 p-0.5 bg-muted/60 border border-border/50 rounded-xl">
              <button
                onClick={() => setActiveTab('logs')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider font-mono transition-all duration-200 cursor-pointer ${
                  activeTab === 'logs'
                    ? 'bg-card text-foreground border border-border/40 shadow-sm'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
                }`}
              >
                <FaTerminal className="text-xs shrink-0" />
                <span>Console Logs</span>
                {isAnalyzing && (
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                )}
              </button>
              
              <button
                onClick={() => setActiveTab('traces')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider font-mono transition-all duration-200 cursor-pointer ${
                  activeTab === 'traces'
                    ? 'bg-card text-foreground border border-border/40 shadow-sm'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
                }`}
              >
                <FaCircleInfo className="text-xs text-brass shrink-0" />
                <span>Agent Traces</span>
                {traces.length > 0 && (
                  <span className="text-[9px] font-mono px-1.5 py-0.2 bg-brass/20 text-brass rounded-full border border-brass/30">
                    {traces.length}
                  </span>
                )}
              </button>

              <button
                onClick={() => setActiveTab('process')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider font-mono transition-all duration-200 cursor-pointer ${
                  activeTab === 'process'
                    ? 'bg-card text-foreground border border-border/40 shadow-sm'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
                }`}
              >
                <FaTasks className="text-xs shrink-0" />
                <span>Process Tracker</span>
              </button>
            </div>
          </div>

          {/* Right Header Actions */}
          <div className="flex items-center gap-2">
            {activeTab === 'logs' && logs.length > 0 && (
              <button
                onClick={clearLogs}
                className="p-1.5 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                title="Clear Logs"
              >
                <FiTrash2 className="text-sm" />
              </button>
            )}

            <button 
              onClick={toggleLogs}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer"
              aria-label="Close Logs Panel"
            >
              <IoClose className="text-xl" />
            </button>
          </div>
        </div>

        {/* Filter bar and search controls (Console tab only) */}
        {activeTab === 'logs' && (
          <div className="flex items-center justify-between gap-3 pt-1">
            {/* Search Input Field */}
            <div className="relative flex-1 max-w-[200px]">
              <FaMagnifyingGlass className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground/60 text-[10px]" />
              <input 
                type="text"
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-background/80 border border-border/50 pl-7 pr-2 py-1 rounded-lg text-[10px] text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-brass/50 focus:ring-1 focus:ring-brass/30 font-mono transition-all"
              />
            </div>

            {/* Level Filters Segmented Pills */}
            <div className="flex items-center gap-1 p-0.5 bg-muted/50 border border-border/40 rounded-lg">
              {(['all', 'info', 'warning', 'error'] as const).map((lvl) => {
                const count = getLogCount(lvl);
                return (
                  <button
                    key={lvl}
                    onClick={() => setFilter(lvl)}
                    className={`px-2 py-0.5 rounded-md text-[9px] font-mono capitalize transition-all duration-200 cursor-pointer flex items-center gap-1 ${
                      filter === lvl 
                        ? 'bg-brass text-slate-950 font-bold shadow-xs' 
                        : 'text-muted-foreground hover:text-foreground hover:bg-muted/40'
                    }`}
                  >
                    <span>{lvl}</span>
                    {count > 0 && (
                      <span className={`text-[8px] px-1 rounded-full ${filter === lvl ? 'bg-brass/20 text-brass font-bold' : 'bg-background/80 text-muted-foreground'}`}>
                        {count}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* ── Terminal Console Logs Stream ────────────────────────── */}
      {activeTab === 'logs' && (
        <div 
          ref={consoleRef}
          className="flex-1 overflow-y-auto p-3.5 font-mono text-[11px] flex flex-col gap-1 bg-card/60 select-text scrollbar-thin scrollbar-thumb-border/30 scrollbar-track-transparent"
        >
          {filteredLogs.map((log) => (
            <div 
              key={log.id} 
              className="flex items-start gap-2.5 py-1 px-2.5 rounded-lg hover:bg-white/5 transition-colors group border border-transparent hover:border-white/5"
            >
              <span className="text-muted-foreground/50 select-none font-light shrink-0 text-[10px]">
                [{log.timestamp}]
              </span>
              
              {getLogIcon(log.type)}
              
              <span className={`flex-1 break-all leading-relaxed ${
                log.type === 'system' ? 'text-muted-foreground font-semibold' :
                log.type === 'success' ? 'text-emerald-400 font-medium' :
                log.type === 'warning' ? 'text-amber-300 font-medium' :
                log.type === 'error' ? 'text-red-400 font-semibold' : 'text-foreground/90'
              }`}>
                {log.text}
              </span>
            </div>
          ))}
          
          {filteredLogs.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full gap-2 text-muted-foreground/40 py-8 select-none">
              <FaTerminal className="text-3xl opacity-30" />
              <span className="text-[11px] font-mono">No console logs available.</span>
            </div>
          )}
        </div>
      )}

      {/* ── Agent Telemetry Traces Timeline View ───────────────────── */}
      {activeTab === 'traces' && (
        <div className="flex-1 overflow-y-auto p-4 font-mono text-[11px] flex flex-col gap-2 bg-card/60 select-text scrollbar-thin scrollbar-thumb-border/30 scrollbar-track-transparent">
          {traces.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-2 text-muted-foreground/40 py-8 select-none">
              <FaCircleInfo className="text-3xl opacity-30 text-brass" />
              <span className="text-[11px] font-mono">No telemetry trace logs recorded yet for this paper.</span>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {traces.map((tr, idx) => (
                <div 
                  key={idx} 
                  className="flex flex-col gap-1 p-2.5 rounded-xl border border-border/40 bg-muted/20 hover:border-brass/40 transition-all"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-brass uppercase text-[10px]">
                      Step: {tr.step_name}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="bg-foreground/10 text-foreground font-mono text-[8px] px-2 py-0.5 rounded-full border border-border/40">
                        {tr.model_used}
                      </span>
                      <span className="bg-emerald-500/15 text-emerald-400 font-mono text-[8px] px-2 py-0.5 rounded-full border border-emerald-500/30 font-bold">
                        {tr.duration_ms}ms
                      </span>
                    </div>
                  </div>
                  <p className="text-foreground/80 font-mono text-[10px] leading-tight">
                    {tr.details}
                  </p>
                  <span className="text-[8px] text-muted-foreground/50 self-end">
                    {tr.timestamp}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Process Tracker (Milestones & Charts) ───────────────── */}
      {activeTab === 'process' && (
        <div className="flex-1 overflow-y-auto p-5 flex flex-col md:flex-row gap-6 bg-black/20 scrollbar-thin scrollbar-thumb-border/30 scrollbar-track-transparent select-none">
          
          {/* Pipeline Step Checklist */}
          <div className="flex-1 flex flex-col gap-3 min-w-[220px] bg-card/40 border border-border/40 p-4 rounded-xl">
            <span className="text-[9.5px] font-mono font-bold tracking-[0.2em] text-brass uppercase">
              {'//'} Pipeline Step Checklist
            </span>
            <MilestoneTracker />
          </div>

          {/* Stats Charts */}
          <div className="w-full md:w-[300px] flex flex-col gap-3 shrink-0 bg-card/40 border border-border/40 p-4 rounded-xl">
            <span className="text-[9.5px] font-mono font-bold tracking-[0.2em] text-brass uppercase">
              {'//'} Analytics Metric Depth
            </span>
            <StatsCharts />
          </div>
        </div>
      )}
    </aside>
  );
};