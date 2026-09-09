"use client";

import React from "react";
import { LogEntry } from "./types";
import { Terminal } from "lucide-react";

interface FlowchartSimulationTerminalProps {
  logs: LogEntry[];
  currentStep: number;
  totalSteps: number;
}

export function FlowchartSimulationTerminal({
  logs,
  currentStep,
  totalSteps,
}: FlowchartSimulationTerminalProps) {
  if (logs.length === 0) return null;

  return (
    <div className="p-4 rounded-xl bg-[#18181B] border border-white/10 mb-6 font-mono text-xs shadow-lg">
      <div className="flex items-center justify-between pb-2 border-b border-white/8 mb-2">
        <div className="flex items-center gap-2 text-[#34D399]">
          <Terminal className="w-3.5 h-3.5" />
          <span className="font-bold">Active Pipeline Execution Trace Log</span>
        </div>
        <span className="text-[10px] text-[#71717A]">
          Step {currentStep + 1} / {totalSteps}
        </span>
      </div>

      <div className="space-y-1 max-h-24 overflow-y-auto pr-2">
        {logs.map((log, i) => (
          <div key={i} className="flex items-center gap-2 text-[#D4D4D8]">
            <span className="text-[#71717A] shrink-0">[{log.time}]</span>
            <span className={log.status === "success" ? "text-[#34D399] font-bold" : "text-[#F4F3EE]"}>
              {log.text}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
