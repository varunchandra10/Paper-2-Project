import os
import json
import datetime
from typing import List, Dict, Any, Optional
from app.core.config import settings


class AgentTracer:
    """Manages telemetry logging for agent execution steps, model router choices,

    step durations, and confidence scores across pipeline runs.
    """

    def __init__(self, traces_dir: str = settings.TRACES_DIR):
        self.traces_dir = traces_dir
        os.makedirs(self.traces_dir, exist_ok=True)

    def _get_trace_file(self, paper_id: str) -> str:
        return os.path.join(self.traces_dir, f"{paper_id}.json")

    def start_trace(self, paper_id: str) -> List[Dict[str, Any]]:
        """Initializes a new trace log for a given paper run."""
        trace_file = self._get_trace_file(paper_id)
        initial_trace = [{
            "step_name": "TRACE_INITIALIZED",
            "status": "success",
            "duration_ms": 0,
            "model_used": "System",
            "confidence": 1.0,
            "details": f"Execution telemetry trace initialized for paper '{paper_id}'.",
            "timestamp": datetime.datetime.now().isoformat()
        }]
        try:
            with open(trace_file, "w", encoding="utf-8") as f:
                json.dump(initial_trace, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[TRACER ERROR] Failed to initialize trace file for '{paper_id}': {e}")
        return initial_trace

    def log_step(
        self,
        paper_id: str,
        step_name: str,
        status: str = "success",
        details: str = "",
        duration_ms: int = 0,
        model_used: str = "qwen2.5-coder:1.5b",
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """Appends a new trace step log to the paper's trace history."""
        if not paper_id:
            return {}
            
        trace_file = self._get_trace_file(paper_id)
        traces = self.get_traces(paper_id)
        
        step_entry = {
            "step_name": step_name,
            "status": status,
            "duration_ms": duration_ms,
            "model_used": model_used,
            "confidence": round(confidence, 2),
            "details": details,
            "timestamp": datetime.datetime.now().isoformat()
        }
        traces.append(step_entry)
        
        try:
            with open(trace_file, "w", encoding="utf-8") as f:
                json.dump(traces, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[TRACER ERROR] Failed to log step for '{paper_id}': {e}")
            
        return step_entry

    def get_traces(self, paper_id: str) -> List[Dict[str, Any]]:
        """Reads trace log steps for a paper from disk."""
        if not paper_id:
            return []
        trace_file = self._get_trace_file(paper_id)
        if os.path.exists(trace_file):
            try:
                with open(trace_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[TRACER WARN] Failed to read trace file for '{paper_id}': {e}")
        return []
