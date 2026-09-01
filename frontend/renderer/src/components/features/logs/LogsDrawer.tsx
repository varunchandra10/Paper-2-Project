import React, { useRef, useEffect } from 'react';
import { useLogsStore } from '../../../store/logsStore';
import { usePanelStore } from '../../../store/panelStore';
import { MilestoneTracker } from '../analysis/MilestoneTracker';
import { StatsCharts } from '../analysis/StatsCharts';
import { 
  IconTerminal, 
  IconSearch, 
  IconInfo2, 
  IconWarning, 
  IconError, 
  IconCheck,
  IconTasks,
  IconClose,
  IconTrash
} from '../../ui/Icons';

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
          const res = await fetch(`${apiBase}/papers/${activePaperId}/execution-traces`);
          if (res.ok) {
            const data = await res.json();
            setTraces(data.traces || []);
          }
        } catch {
          // Ignore trace polling errors silently
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
        return <IconCheck className="text-emerald-400 text-[10px] shrink-0 mt-0.5" />;
      case 'warning':
        return <IconWarning className="text-amber-400 text-[10px] shrink-0 mt-0.5" />;
      case 'error':
        return <IconError className="text-red-400 text-[10px] shrink-0 mt-0.5" />;
      case 'info':
        return <IconInfo2 className="text-[var(--accent)] text-[10px] shrink-0 mt-0.5" />;
      default:
        return <span className="text-[var(--text-muted)] font-bold select-none text-[10px] shrink-0">&gt;</span>;
    }
  };

  const getLogCount = (type: string) => {
    if (type === 'all') return logs.length;
    return logs.filter((l) => l.type === type).length;
  };

  return (
    <aside 
      className={`absolute left-0 right-0 bottom-0 h-[380px] bg-[var(--bg-card)] border-t app-border shadow-[0_-12px_40px_rgba(0,0,0,0.2)] backdrop-blur-2xl flex flex-col z-30 transform transition-all duration-300 ease-in-out rounded-t-2xl select-none text-[var(--text-main)] ${
        isLogsOpen 
          ? 'translate-y-0 opacity-100' 
          : 'translate-y-full opacity-0 pointer-events-none'
      }`}
      aria-label="System Logs Console"
    >
      {/* ── Header Controls & Tab Triggers ────────────────────────── */}
      <div className="flex flex-col gap-2.5 px-4 py-3 border-b app-border bg-[var(--bg-base)] shrink-0">
        <div className="flex justify-between items-center">
          
          {/* Main Navigation Tabs */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 p-0.5 bg-[var(--bg-card)] border app-border rounded-xl">
              <button
                onClick={() => setActiveTab('logs')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider font-mono transition-all duration-200 cursor-pointer ${
                  activeTab === 'logs'
                    ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)] shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)]'
                }`}
              >
                <IconTerminal className="text-xs shrink-0" />
                <span>Console Logs</span>
                {isAnalyzing && (
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                )}
              </button>
              
              <button
                onClick={() => setActiveTab('traces')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider font-mono transition-all duration-200 cursor-pointer ${
                  activeTab === 'traces'
                    ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)] shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)]'
                }`}
              >
                <IconInfo2 className="text-xs text-[var(--accent)] shrink-0" />
                <span>Agent Traces</span>
                {traces.length > 0 && (
                  <span className="text-[9px] font-mono px-1.5 py-0.2 bg-[var(--accent-subtle)] text-[var(--accent)] rounded-full border border-[var(--accent-border)]">
                    {traces.length}
                  </span>
                )}
              </button>

              <button
                onClick={() => setActiveTab('process')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider font-mono transition-all duration-200 cursor-pointer ${
                  activeTab === 'process'
                    ? 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--accent-border)] shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)]'
                }`}
              >
                <IconTasks className="text-xs shrink-0" />
                <span>Process Tracker</span>
              </button>
            </div>
          </div>

          {/* Right Header Actions */}
          <div className="flex items-center gap-2">
            {activeTab === 'logs' && logs.length > 0 && (
              <button
                onClick={clearLogs}
                className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                title="Clear Logs"
              >
                <IconTrash className="text-sm" />
              </button>
            )}

            <button 
              onClick={toggleLogs}
              className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)] transition-colors cursor-pointer"
              aria-label="Close Logs Panel"
            >
              <IconClose className="text-xl" />
            </button>
          </div>
        </div>

        {/* Filter bar and search controls (Console tab only) */}
        {activeTab === 'logs' && (
          <div className="flex items-center justify-between gap-3 pt-1">
            {/* Search Input Field */}
            <div className="relative flex-1 max-w-[200px]">
              <IconSearch className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-[10px]" />
              <input 
                type="text"
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[var(--bg-base)] border app-border pl-7 pr-2 py-1 rounded-lg text-[10px] text-[var(--text-main)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] font-mono transition-all"
              />
            </div>

            {/* Level Filters Segmented Pills */}
            <div className="flex items-center gap-1 p-0.5 bg-[var(--bg-card)] border app-border rounded-lg">
              {(['all', 'info', 'warning', 'error'] as const).map((lvl) => {
                const count = getLogCount(lvl);
                return (
                  <button
                    key={lvl}
                    onClick={() => setFilter(lvl)}
                    className={`px-2 py-0.5 rounded-md text-[9px] font-mono capitalize transition-all duration-200 cursor-pointer flex items-center gap-1 ${
                      filter === lvl 
                        ? 'bg-[var(--accent)] text-white font-bold shadow-xs' 
                        : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--accent-subtle)]'
                    }`}
                  >
                    <span>{lvl}</span>
                    {count > 0 && (
                      <span className={`text-[8px] px-1 rounded-full ${filter === lvl ? 'bg-white/20 text-white font-bold' : 'bg-[var(--bg-base)] text-[var(--text-muted)]'}`}>
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
          className="flex-1 overflow-y-auto p-3.5 font-mono text-[11px] flex flex-col gap-1 bg-[var(--bg-card)] select-text scrollbar-thin scrollbar-thumb-[var(--border-color)] scrollbar-track-transparent"
        >
          {filteredLogs.map((log) => (
            <div 
              key={log.id} 
              className="flex items-start gap-2.5 py-1 px-2.5 rounded-lg hover:bg-[var(--accent-subtle)] transition-colors group border border-transparent hover:border-[var(--accent-border)]"
            >
              <span className="text-[var(--text-muted)] opacity-60 select-none font-light shrink-0 text-[10px]">
                [{log.timestamp}]
              </span>
              
              {getLogIcon(log.type)}
              
              <span className={`flex-1 break-all leading-relaxed ${
                log.type === 'system' ? 'text-[var(--text-muted)] font-semibold' :
                log.type === 'success' ? 'text-emerald-400 font-medium' :
                log.type === 'warning' ? 'text-amber-400 font-medium' :
                log.type === 'error' ? 'text-red-400 font-semibold' : 'text-[var(--text-main)]'
              }`}>
                {log.text}
              </span>
            </div>
          ))}
          
          {filteredLogs.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full gap-2 text-[var(--text-muted)] py-8 select-none">
              <IconTerminal className="text-3xl opacity-30" />
              <span className="text-[11px] font-mono">No console logs available.</span>
            </div>
          )}
        </div>
      )}

      {/* ── Agent Telemetry Traces Timeline View ───────────────────── */}
      {activeTab === 'traces' && (
        <div className="flex-1 overflow-y-auto p-4 font-mono text-[11px] flex flex-col gap-2 bg-[var(--bg-card)] select-text scrollbar-thin scrollbar-thumb-[var(--border-color)] scrollbar-track-transparent">
          {traces.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-2 text-[var(--text-muted)] py-8 select-none">
              <IconInfo2 className="text-3xl opacity-30 text-[var(--accent)]" />
              <span className="text-[11px] font-mono">No telemetry trace logs recorded yet for this paper.</span>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {traces.map((tr, idx) => (
                <div 
                  key={idx} 
                  className="flex flex-col gap-1 p-2.5 rounded-xl border app-border bg-[var(--bg-base)] hover:border-[var(--accent-border)] transition-all"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-[var(--accent)] uppercase text-[10px]">{tr.agent_name || 'Agent'}</span>
                    <span className="text-[9px] text-[var(--text-muted)]">{tr.step_name}</span>
                  </div>
                  <div className="text-[10px] text-[var(--text-main)]">{tr.output || tr.details}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Process Tracker Tab ────────────────────────────────────── */}
      {activeTab === 'process' && (
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 bg-[var(--bg-card)] scrollbar-thin scrollbar-thumb-[var(--border-color)] scrollbar-track-transparent">
          <MilestoneTracker />
          <StatsCharts />
        </div>
      )}
    </aside>
  );
};