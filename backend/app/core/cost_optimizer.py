"""
Phase 14: Cost & Resource Optimization Service.

Provides comprehensive token tracking, latency measurement, duplicate call detection,
prompt completion caching, paper ingestion caching (SHA-256 hash deduplication),
embedding batching optimization, and model cost analysis.
"""

import os
import json
import time
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.core.config import settings
from app.schemas.paper import PaperDocument

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(settings.STORAGE_DIR, "paper_cache")
PROMPT_CACHE_DIR = os.path.join(settings.STORAGE_DIR, "prompt_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(PROMPT_CACHE_DIR, exist_ok=True)

# Standard industry pricing per 1 Million tokens (USD)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # Local models: 0 cloud infrastructure cost
    "local": {"input_per_million": 0.0, "output_per_million": 0.0},
    "ollama": {"input_per_million": 0.0, "output_per_million": 0.0},
    "qwen2.5:7b": {"input_per_million": 0.0, "output_per_million": 0.0},
    "qwen2.5-coder:1.5b": {"input_per_million": 0.0, "output_per_million": 0.0},
    "nomic-embed-text": {"input_per_million": 0.0, "output_per_million": 0.0},
    # Groq LPU
    "groq": {"input_per_million": 0.59, "output_per_million": 0.79},
    "llama-3.3-70b-versatile": {"input_per_million": 0.59, "output_per_million": 0.79},
    "qwen-2.5-32b": {"input_per_million": 0.59, "output_per_million": 0.79},
    # Google Gemini
    "gemini": {"input_per_million": 0.15, "output_per_million": 0.60},
    "gemini-2.0-flash": {"input_per_million": 0.15, "output_per_million": 0.60},
    "gemini-2.5-flash": {"input_per_million": 0.15, "output_per_million": 0.60},
    # Hugging Face Serverless
    "huggingface": {"input_per_million": 0.20, "output_per_million": 0.20},
    "Qwen/Qwen2.5-Coder-32B-Instruct": {"input_per_million": 0.20, "output_per_million": 0.20},
    # OpenRouter
    "openrouter": {"input_per_million": 0.15, "output_per_million": 0.60},
    # Default fallback
    "default": {"input_per_million": 0.20, "output_per_million": 0.50}
}


class CostAndResourceOptimizer:
    """
    Centralized controller for measuring and optimizing model tokens,
    latency, duplicate invocations, and paper ingestion deduplication.
    """

    def __init__(self, cache_dir: str = CACHE_DIR, prompt_cache_dir: str = PROMPT_CACHE_DIR):
        self.cache_dir = cache_dir
        self.prompt_cache_dir = prompt_cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.prompt_cache_dir, exist_ok=True)

        # In-memory fast cache layers
        self._prompt_cache: Dict[str, Dict[str, Any]] = {}
        self._embedding_cache: Dict[str, List[float]] = {}
        self._seen_call_signatures: Dict[str, int] = {}

        # Telemetry metrics
        self.total_invocations: int = 0
        self.duplicate_calls_detected: int = 0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_cost_usd: float = 0.0
        self.saved_tokens: int = 0
        self.saved_cost_usd: float = 0.0
        self.saved_latency_ms: float = 0.0
        self.latency_by_stage: Dict[str, List[float]] = {}
        self.tokens_by_model: Dict[str, Dict[str, int]] = {}

    # ---------------------------------------------------------
    # 1. Token Estimation & Cost Calculation
    # ---------------------------------------------------------
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimates token count (~4 characters per token heuristic for code/text)."""
        if not text:
            return 0
        # Average English/code token is ~3.8 to 4.2 characters
        return max(1, len(text.strip()) // 4)

    def calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Calculates precise dollar cost based on model pricing matrix."""
        # Find matching pricing key
        pricing = MODEL_PRICING.get("default")
        model_lower = (model_name or "").lower()

        for key, p in MODEL_PRICING.items():
            if key.lower() in model_lower:
                pricing = p
                break

        in_cost = (input_tokens / 1_000_000.0) * pricing["input_per_million"]
        out_cost = (output_tokens / 1_000_000.0) * pricing["output_per_million"]
        return round(in_cost + out_cost, 6)

    def record_call(
        self,
        stage: str,
        model_name: str,
        prompt: str,
        completion: str,
        duration_ms: float
    ) -> Dict[str, Any]:
        """
        Records an LLM invocation, computes tokens & cost,
        and detects duplicate/repeated calls.
        """
        in_tokens = self.estimate_tokens(prompt)
        out_tokens = self.estimate_tokens(completion)
        cost = self.calculate_cost(model_name, in_tokens, out_tokens)

        # Call signature for duplicate detection
        sig = hashlib.sha256(f"{model_name}:{prompt}".encode("utf-8")).hexdigest()
        is_duplicate = False
        if sig in self._seen_call_signatures:
            self._seen_call_signatures[sig] += 1
            self.duplicate_calls_detected += 1
            is_duplicate = True
        else:
            self._seen_call_signatures[sig] = 1

        self.total_invocations += 1
        self.total_input_tokens += in_tokens
        self.total_output_tokens += out_tokens
        self.total_cost_usd = round(self.total_cost_usd + cost, 6)

        # Latency tracking
        if stage not in self.latency_by_stage:
            self.latency_by_stage[stage] = []
        self.latency_by_stage[stage].append(duration_ms)

        # Model breakdown
        m_key = model_name or "unknown"
        if m_key not in self.tokens_by_model:
            self.tokens_by_model[m_key] = {"input_tokens": 0, "output_tokens": 0, "calls": 0}
        self.tokens_by_model[m_key]["input_tokens"] += in_tokens
        self.tokens_by_model[m_key]["output_tokens"] += out_tokens
        self.tokens_by_model[m_key]["calls"] += 1

        return {
            "stage": stage,
            "model": model_name,
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "total_tokens": in_tokens + out_tokens,
            "cost_usd": cost,
            "duration_ms": duration_ms,
            "is_duplicate": is_duplicate
        }

    # ---------------------------------------------------------
    # 2. Prompt Completion Caching
    # ---------------------------------------------------------
    def get_cached_completion(self, model_name: str, prompt: str) -> Optional[str]:
        """Checks if identical prompt was already computed for this model."""
        key = hashlib.sha256(f"{model_name}:{prompt.strip()}".encode("utf-8")).hexdigest()

        # Check in-memory
        if key in self._prompt_cache:
            entry = self._prompt_cache[key]
            self.saved_tokens += entry["saved_tokens"]
            self.saved_cost_usd = round(self.saved_cost_usd + entry["saved_cost"], 6)
            self.saved_latency_ms += entry["saved_latency_ms"]
            return entry["completion"]

        # Check disk
        path = os.path.join(self.prompt_cache_dir, f"{key}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                self._prompt_cache[key] = entry
                self.saved_tokens += entry.get("saved_tokens", 0)
                self.saved_cost_usd = round(self.saved_cost_usd + entry.get("saved_cost", 0.0), 6)
                self.saved_latency_ms += entry.get("saved_latency_ms", 0.0)
                return entry.get("completion")
            except Exception as e:
                logger.warning(f"[CostOptimizer] Failed to read prompt cache {key}: {e}")

        return None

    def set_cached_completion(
        self,
        model_name: str,
        prompt: str,
        completion: str,
        latency_ms: float = 1000.0
    ):
        """Saves prompt completion to fast cache."""
        key = hashlib.sha256(f"{model_name}:{prompt.strip()}".encode("utf-8")).hexdigest()
        in_tok = self.estimate_tokens(prompt)
        out_tok = self.estimate_tokens(completion)
        cost = self.calculate_cost(model_name, in_tok, out_tok)

        entry = {
            "model": model_name,
            "completion": completion,
            "saved_tokens": in_tok + out_tok,
            "saved_cost": cost,
            "saved_latency_ms": latency_ms,
            "timestamp": time.time()
        }
        self._prompt_cache[key] = entry

        # Save to disk
        path = os.path.join(self.prompt_cache_dir, f"{key}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2)
        except Exception as e:
            logger.warning(f"[CostOptimizer] Failed to write prompt cache {key}: {e}")

    # ---------------------------------------------------------
    # 3. Unchanged Paper Ingestion Caching (Avoid Reprocessing)
    # ---------------------------------------------------------
    def get_cached_paper_ingestion(self, pdf_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached ingestion state if the paper PDF SHA-256 hash was
        previously ingested and its vector index exists.
        Avoids redundant PDF parsing, chunking, embedding, and LLM extraction!
        """
        if not pdf_hash:
            return None

        cache_file = os.path.join(self.cache_dir, f"{pdf_hash}.json")
        if not os.path.exists(cache_file):
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            paper_id = data.get("paper_id")
            # Verify that vector storage file also exists
            from app.core.config import settings
            vdb_dir = getattr(settings, "RAG_EMBEDDINGS_DIR", os.path.join(settings.STORAGE_DIR, "rag_based"))
            vdb_path = os.path.join(vdb_dir, f"{paper_id}.json")
            if not os.path.exists(vdb_path):
                logger.info(f"[CostOptimizer] Paper cache {pdf_hash[:10]} found but vector store missing. Re-ingesting.")
                return None

            # Deserialization of PaperDocument
            doc_dict = data.get("paper_doc")
            paper_doc = PaperDocument.model_validate(doc_dict)

            # Record savings
            saved_tok = data.get("estimated_tokens_saved", 8000)
            saved_lat = data.get("estimated_latency_saved_ms", 3500.0)
            self.saved_tokens += saved_tok
            self.saved_cost_usd = round(self.saved_cost_usd + self.calculate_cost("gemini", saved_tok, 1000), 6)
            self.saved_latency_ms += saved_lat

            logger.info(f"[CostOptimizer] CACHE HIT for paper hash {pdf_hash[:10]} (Paper ID: {paper_id}). Reprocessing avoided!")
            return {
                "paper_doc": paper_doc,
                "raw_sections": data.get("raw_sections", {}),
                "metadata": data.get("metadata", {}),
                "cache_hit": True
            }
        except Exception as e:
            logger.error(f"[CostOptimizer] Error loading paper cache for hash {pdf_hash}: {e}")
            return None

    def cache_paper_ingestion(
        self,
        pdf_hash: str,
        paper_doc: PaperDocument,
        raw_sections: Dict[str, str],
        metadata: Dict[str, Any],
        estimated_tokens_saved: int = 8000,
        estimated_latency_ms: float = 3500.0
    ):
        """Atomically caches ingested paper state keyed by PDF SHA-256 hash."""
        if not pdf_hash:
            return

        cache_file = os.path.join(self.cache_dir, f"{pdf_hash}.json")
        payload = {
            "pdf_hash": pdf_hash,
            "paper_id": paper_doc.paper_id,
            "paper_doc": paper_doc.model_dump(),
            "raw_sections": raw_sections,
            "metadata": metadata,
            "estimated_tokens_saved": estimated_tokens_saved,
            "estimated_latency_saved_ms": estimated_latency_ms,
            "timestamp": time.time()
        }

        temp_file = f"{cache_file}.tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            os.replace(temp_file, cache_file)
            logger.info(f"[CostOptimizer] Cached paper ingestion for hash {pdf_hash[:10]} (ID: {paper_doc.paper_id})")
        except Exception as e:
            logger.error(f"[CostOptimizer] Failed to write paper cache {pdf_hash}: {e}")

    # ---------------------------------------------------------
    # 4. Batch Embeddings & Chunk Cache
    # ---------------------------------------------------------
    def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Returns cached embedding vector for identical chunk text."""
        h = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
        return self._embedding_cache.get(h)

    def cache_embedding(self, text: str, vector: List[float]):
        """Caches embedding vector in memory."""
        h = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
        self._embedding_cache[h] = vector

    # ---------------------------------------------------------
    # 5. Summary & Telemetry Reporting
    # ---------------------------------------------------------
    def get_optimization_report(self) -> Dict[str, Any]:
        """Returns consolidated metrics across all optimization strategies."""
        avg_latency = {}
        for stage, latencies in self.latency_by_stage.items():
            avg_latency[stage] = round(sum(latencies) / max(1, len(latencies)), 2)

        return {
            "total_invocations": self.total_invocations,
            "duplicate_calls_detected": self.duplicate_calls_detected,
            "tokens": {
                "input_tokens": self.total_input_tokens,
                "output_tokens": self.total_output_tokens,
                "total_tokens_used": self.total_input_tokens + self.total_output_tokens,
                "tokens_saved_via_caching": self.saved_tokens
            },
            "costs_usd": {
                "total_incurred": round(self.total_cost_usd, 4),
                "total_saved_via_caching": round(self.saved_cost_usd, 4)
            },
            "latency": {
                "saved_latency_ms": round(self.saved_latency_ms, 2),
                "saved_latency_seconds": round(self.saved_latency_ms / 1000.0, 2),
                "average_latency_by_stage_ms": avg_latency
            },
            "tokens_by_model": self.tokens_by_model,
            "model_pricing_reference": MODEL_PRICING
        }


# Global singleton instance
cost_optimizer = CostAndResourceOptimizer()
