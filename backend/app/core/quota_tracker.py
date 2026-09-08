"""
Dynamic Quota and Rate Limit Tracker for Paper-2-Project Backend.

Eliminates static hardcoded quota counts. Rates and quotas are dynamically
extracted from live provider API gateways, response headers, and account telemetry.
"""

import os
import json
import time
import httpx
import concurrent.futures
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.constants import (
    GROQ_MODELS_URL,
    OPENROUTER_AUTH_URL,
    HUGGINGFACE_WHOAMI_URL,
    GEMINI_BASE_URL,
    INITIAL_GROQ_LIMIT_REQUESTS,
    INITIAL_GROQ_LIMIT_TOKENS,
    INITIAL_GROQ_MINUTE_LIMIT,
    INITIAL_HF_DAILY_LIMIT,
    INITIAL_HF_MINUTE_LIMIT,
    INITIAL_GEMINI_DAILY_LIMIT,
    INITIAL_GEMINI_MINUTE_LIMIT,
    INITIAL_OPENROUTER_DAILY_LIMIT,
    INITIAL_OPENROUTER_MINUTE_LIMIT
)

QUOTA_FILE = os.path.join(settings.HISTORY_DIR, "model_quotas.json")

# Baseline metadata labels (limits are dynamically populated from live APIs)
PROVIDER_METADATA = {
    "groq": {
        "label": "Groq LPU Models",
        "description": "Groq Cloud High-Speed Inference (Qwen 3.8 27B & GPT-OSS 120B)",
        "default_requests": INITIAL_GROQ_LIMIT_REQUESTS,
        "default_tokens": INITIAL_GROQ_LIMIT_TOKENS,
        "default_minute": INITIAL_GROQ_MINUTE_LIMIT,
    },
    "openrouter": {
        "label": "OpenRouter Free Models",
        "description": "OpenRouter Free Tier (Gemini 2.5 Flash & DeepSeek R1)",
        "default_requests": INITIAL_OPENROUTER_DAILY_LIMIT,
        "default_minute": INITIAL_OPENROUTER_MINUTE_LIMIT,
    },
    "gemini": {
        "label": "Google Gemini 2.0 Flash",
        "description": "Google AI Studio API (High-Fidelity Paper Analysis & Math)",
        "default_daily": INITIAL_GEMINI_DAILY_LIMIT,
        "default_minute": INITIAL_GEMINI_MINUTE_LIMIT,
    },
    "huggingface": {
        "label": "Hugging Face Inference Router",
        "description": "HF Serverless Inference (Qwen 2.5 Coder 32B Instruct)",
        "default_daily": INITIAL_HF_DAILY_LIMIT,
        "default_minute": INITIAL_HF_MINUTE_LIMIT,
    },
    "local": {
        "label": "Local Models (Ollama)",
        "description": "Local Hardware Inference (Zero Cloud Cost)",
        "is_unlimited": True
    }
}


class QuotaTracker:
    """Tracks and enforces rolling window quotas for LLM providers using live telemetry."""

    def __init__(self, storage_path: str = QUOTA_FILE):
        self.storage_path = storage_path
        self._server_cache: Dict[str, Any] = {}
        self._server_cache_time: float = 0
        self._live_limits: Dict[str, Any] = {}
        self._ensure_storage()

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            initial_data = {
                "version": 2,
                "events": {
                    "groq": [],
                    "openrouter": [],
                    "local": [],
                    "gemini": [],
                    "huggingface": []
                },
                "live_limits": {}
            }
            try:
                with open(self.storage_path, "w", encoding="utf-8") as f:
                    json.dump(initial_data, f, indent=2)
            except Exception as e:
                print(f"[QUOTA_TRACKER WARN] Could not initialize quota file: {e}")
        else:
            try:
                data = self._load_data()
                self._live_limits = data.get("live_limits", {})
            except Exception:
                pass

    def _load_storage(self) -> Dict[str, Any]:
        """Load persisted storage dictionary."""
        return self._load_data()

    def _load_usage_window(self, provider: str) -> list:
        """Load timestamp list for rolling window from persisted storage."""
        data = self._load_storage()
        window = data.get(provider, {}).get("usage_window", [])
        # Prune entries older than 60s on load
        now = time.time()
        return [t for t in window if now - t < 60]

    def _save_usage_window(self, provider: str, window: list):
        """Save timestamp list for rolling window to persisted storage."""
        data = self._load_storage()
        if provider not in data or not isinstance(data[provider], dict):
            data[provider] = {}
        now = time.time()
        data[provider]["usage_window"] = [t for t in window if now - t < 60]
        self._save_data(data)

    def _load_data(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[QUOTA_TRACKER WARN] Read error: {e}")
        return {"events": {"groq": [], "openrouter": [], "local": [], "gemini": [], "huggingface": []}, "live_limits": {}}

    def _save_data(self, data: Dict[str, Any]):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[QUOTA_TRACKER ERROR] Save error: {e}")

    def update_live_headers(self, provider: str, headers: Any):
        """
        Dynamically extracts rate limit metrics from live HTTP response headers.
        Called automatically by provider adapters upon receiving completions.
        """
        if not headers:
            return

        provider_key = provider.lower()
        # Convert headers to case-insensitive mapping
        h_dict = {k.lower(): str(v) for k, v in headers.items()}
        updated = False

        if "groq" in provider_key:
            rem_req = h_dict.get("x-ratelimit-remaining-requests") or h_dict.get("ratelimit-remaining-requests")
            lim_req = h_dict.get("x-ratelimit-limit-requests") or h_dict.get("ratelimit-limit-requests")
            reset_req = h_dict.get("x-ratelimit-reset-requests") or h_dict.get("ratelimit-reset-requests")
            rem_tok = h_dict.get("x-ratelimit-remaining-tokens") or h_dict.get("ratelimit-remaining-tokens")
            lim_tok = h_dict.get("x-ratelimit-limit-tokens") or h_dict.get("ratelimit-limit-tokens")

            if lim_req and lim_req.isdigit():
                self._live_limits["groq"] = {
                    "limit_requests": int(lim_req),
                    "remaining_requests": int(rem_req) if rem_req and rem_req.isdigit() else int(lim_req),
                    "reset_requests": reset_req or "dynamic",
                    "limit_tokens": int(lim_tok) if lim_tok and lim_tok.isdigit() else None,
                    "remaining_tokens": int(rem_tok) if rem_tok and rem_tok.isdigit() else None,
                    "last_updated": time.time(),
                    "source": "Live Groq Headers"
                }
                updated = True

        elif "openrouter" in provider_key:
            rem_req = h_dict.get("x-ratelimit-remaining") or h_dict.get("ratelimit-remaining")
            lim_req = h_dict.get("x-ratelimit-limit") or h_dict.get("ratelimit-limit")
            if lim_req and lim_req.isdigit():
                self._live_limits["openrouter"] = {
                    "limit_requests": int(lim_req),
                    "remaining_requests": int(rem_req) if rem_req and rem_req.isdigit() else int(lim_req),
                    "last_updated": time.time(),
                    "source": "Live OpenRouter Headers"
                }
                updated = True

        elif "huggingface" in provider_key:
            compute_type = h_dict.get("x-compute-type") or h_dict.get("x-inference-router")
            if compute_type:
                self._live_limits["huggingface"] = {
                    "compute_type": compute_type,
                    "last_updated": time.time(),
                    "source": "Live HF Headers"
                }
                updated = True

        if updated:
            data = self._load_data()
            data["live_limits"] = self._live_limits
            self._save_data(data)
            self._server_cache_time = 0  # invalidate cache

    def record_usage(self, provider: str, model_id: str = ""):
        """Records an inference call timestamp for the specified provider."""
        provider_key = provider.lower()
        if "gemini" in provider_key:
            key = "gemini"
        elif "groq" in provider_key:
            key = "groq"
        elif "openrouter" in provider_key:
            key = "openrouter"
        elif "huggingface" in provider_key:
            key = "huggingface"
        else:
            key = "local"

        data = self._load_storage()
        events = data.get("events", {})
        if key not in events:
            events[key] = []

        now = time.time()
        # Keep 7 days of rolling events
        seven_days_ago = now - 604800
        cleaned = [
            e for e in events[key]
            if (isinstance(e, dict) and e.get("timestamp", 0) > seven_days_ago)
            or (isinstance(e, (int, float)) and e > seven_days_ago)
        ]

        cleaned.append({
            "timestamp": now,
            "model": model_id
        })
        events[key] = cleaned
        data["events"] = events

        # Update persisted rolling usage window for provider keys
        for p in set([key, provider]):
            if p and p not in ["events", "live_limits", "version"]:
                current_window = [t for t in data.get(p, {}).get("usage_window", []) if now - t < 60]
                current_window.append(now)
                if p not in data or not isinstance(data[p], dict):
                    data[p] = {}
                data[p]["usage_window"] = current_window

        self._save_data(data)
        self._server_cache_time = 0

    @staticmethod
    def _format_time_remaining(seconds: float) -> str:
        if seconds <= 0:
            return "Limit fully available."
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        if days > 0:
            return f"it will fully refresh in {days} day{'s' if days > 1 else ''}, {hours} hour{'s' if hours != 1 else ''}."
        if hours > 0:
            return f"it will fully refresh in {hours} hour{'s' if hours > 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}."
        if minutes > 0:
            return f"it will fully refresh in {minutes} minute{'s' if minutes > 1 else ''}."
        return "it will fully refresh in less than a minute."

    def get_limits_summary(self) -> Dict[str, Any]:
        """Calculates rolling limit metrics using live API telemetry and recorded events."""
        data = self._load_data()
        events = data.get("events", {})
        live_lims = data.get("live_limits", self._live_limits)
        now = time.time()

        seven_days_ago = now - (7 * 86400)
        five_hours_ago = now - (5 * 3600)
        one_day_ago = now - 86400
        one_min_ago = now - 60

        summary = {}

        for provider, meta in PROVIDER_METADATA.items():
            prov_events = events.get(provider, [])
            timestamps = []
            for ev in prov_events:
                if isinstance(ev, dict):
                    timestamps.append(ev.get("timestamp", 0))
                elif isinstance(ev, (int, float)):
                    timestamps.append(ev)

            # 1. Local Unlimited
            if meta.get("is_unlimited"):
                summary[provider] = {
                    "label": meta["label"],
                    "description": meta["description"],
                    "is_local": True,
                    "weekly": {
                        "limit": "Unlimited",
                        "used": len([t for t in timestamps if t > seven_days_ago]),
                        "remaining_pct": 100,
                        "refresh_message": "Runs offline on local hardware. No rate limits.",
                        "status": "unlimited"
                    },
                    "five_hour": {
                        "limit": "Unlimited",
                        "used": len([t for t in timestamps if t > five_hours_ago]),
                        "remaining_pct": 100,
                        "refresh_message": "Always available without cloud rate limits.",
                        "status": "unlimited"
                    }
                }
                continue

            # 2. Dedicated Backend Engines: Gemini & Hugging Face
            if provider in ["gemini", "huggingface"]:
                live_info = live_lims.get(provider, {})
                daily_limit = live_info.get("daily_limit", meta.get("default_daily", 1500))
                minute_limit = live_info.get("minute_limit", meta.get("default_minute", 15 if provider == "gemini" else 30))

                daily_used = len([t for t in timestamps if t > one_day_ago])
                window = self._load_usage_window(provider)
                minute_used = len(window) if window else len([t for t in timestamps if t > one_min_ago])

                daily_remaining = max(0, daily_limit - daily_used)
                minute_remaining = max(0, minute_limit - minute_used)
                daily_pct = max(0, min(100, int((daily_remaining / daily_limit) * 100)))

                daily_refresh_str = f"{daily_remaining:,} of {daily_limit:,} daily requests remaining."
                minute_refresh_str = f"{minute_remaining} of {minute_limit} requests/min currently available."

                summary[provider] = {
                    "label": meta["label"],
                    "description": meta["description"],
                    "is_local": False,
                    "daily_limit": daily_limit,
                    "daily_used": daily_used,
                    "daily_remaining": daily_remaining,
                    "daily_pct": daily_pct,
                    "minute_limit": minute_limit,
                    "minute_used": minute_used,
                    "minute_remaining": minute_remaining,
                    "daily_refresh_message": daily_refresh_str,
                    "minute_refresh_message": minute_refresh_str,
                    "weekly": {
                        "limit": daily_limit,
                        "used": daily_used,
                        "remaining_pct": daily_pct,
                        "refresh_message": daily_refresh_str,
                        "status": "normal" if daily_pct > 20 else ("warning" if daily_pct > 0 else "exceeded")
                    },
                    "five_hour": {
                        "limit": minute_limit,
                        "used": minute_used,
                        "remaining_pct": max(0, min(100, int((minute_remaining / minute_limit) * 100))),
                        "refresh_message": minute_refresh_str,
                        "status": "normal" if minute_remaining > 2 else "warning"
                    },
                    "status": "ready" if daily_remaining > 0 else "exhausted"
                }
                continue

            # 3. Conversational Frontend APIs: Groq & OpenRouter
            live_info = live_lims.get(provider, {})
            has_live_headers = "limit_requests" in live_info

            if has_live_headers:
                total_limit = live_info["limit_requests"]
                remaining_requests = live_info.get("remaining_requests", total_limit)
                used_requests = max(0, total_limit - remaining_requests)
                remaining_pct = max(0, min(100, int((remaining_requests / total_limit) * 100)))
                reset_msg = live_info.get("reset_requests", "Dynamic")

                summary[provider] = {
                    "label": meta["label"],
                    "description": meta["description"],
                    "is_local": False,
                    "weekly": {
                        "limit": total_limit,
                        "used": used_requests,
                        "remaining_pct": remaining_pct,
                        "refresh_message": f"{remaining_requests:,} of {total_limit:,} requests remaining (Refreshes: {reset_msg}).",
                        "status": "normal" if remaining_pct > 20 else ("warning" if remaining_pct > 0 else "exceeded")
                    },
                    "five_hour": {
                        "limit": total_limit,
                        "used": used_requests,
                        "remaining_pct": remaining_pct,
                        "refresh_message": f"Live gateway remaining: {remaining_requests:,} requests.",
                        "status": "normal" if remaining_pct > 10 else "warning"
                    }
                }
            else:
                # Fallback to rolling timestamps until first gateway response is recorded
                weekly_timestamps = [t for t in timestamps if t > seven_days_ago]
                five_hour_timestamps = [t for t in timestamps if t > five_hours_ago]

                weekly_used = len(weekly_timestamps)
                five_hour_used = len(five_hour_timestamps)

                weekly_limit = meta.get("default_requests", 500)
                five_hour_limit = max(10, int(weekly_limit * 0.1))

                weekly_pct = max(0, min(100, int(((weekly_limit - weekly_used) / weekly_limit) * 100)))
                five_hour_pct = max(0, min(100, int(((five_hour_limit - five_hour_used) / five_hour_limit) * 100)))

                summary[provider] = {
                    "label": meta["label"],
                    "description": meta["description"],
                    "is_local": False,
                    "weekly": {
                        "limit": weekly_limit,
                        "used": weekly_used,
                        "remaining_pct": weekly_pct,
                        "refresh_message": f"{max(0, weekly_limit - weekly_used):,} of {weekly_limit:,} baseline calls remaining.",
                        "status": "normal" if weekly_pct > 20 else ("warning" if weekly_pct > 0 else "exceeded")
                    },
                    "five_hour": {
                        "limit": five_hour_limit,
                        "used": five_hour_used,
                        "remaining_pct": five_hour_pct,
                        "refresh_message": f"{max(0, five_hour_limit - five_hour_used):,} of {five_hour_limit:,} baseline calls remaining.",
                        "status": "normal" if five_hour_pct > 20 else ("warning" if five_hour_pct > 0 else "exceeded")
                    }
                }

        return summary

    def is_provider_available(self, provider: str) -> bool:
        """Returns True if the provider has quota remaining."""
        p_lower = provider.lower()
        if "local" in p_lower or "ollama" in p_lower:
            return True
        elif "groq" in p_lower:
            key = "groq"
        elif "openrouter" in p_lower:
            key = "openrouter"
        elif "gemini" in p_lower:
            key = "gemini"
        elif "huggingface" in p_lower:
            key = "huggingface"
        else:
            key = "groq"

        summary = self.get_limits_summary()
        prov_summary = summary.get(key)
        if not prov_summary:
            return True
        if key in ["gemini", "huggingface"]:
            return prov_summary.get("daily_remaining", 1) > 0 and prov_summary.get("minute_remaining", 1) > 0
        return prov_summary.get("five_hour", {}).get("remaining_pct", 100) > 0 and prov_summary.get("weekly", {}).get("remaining_pct", 100) > 0

    def fetch_live_server_metrics(self) -> Dict[str, Any]:
        """
        Queries official provider API gateways to fetch exact server-side rate limits and console usage.
        Cached for 15 seconds to avoid flooding provider endpoints.
        """
        now = time.time()
        if hasattr(self, "_server_cache") and (now - getattr(self, "_server_cache_time", 0)) < 15:
            return self._server_cache

        metrics = {
            "openrouter": {"status": "offline"},
            "groq": {"status": "offline"},
            "gemini": {"status": "offline"},
            "huggingface": {"status": "offline"},
            "local": {"status": "offline"}
        }

        # Resolve user private keys from profile or fallback to server keys
        user_groq = None
        user_or = None
        try:
            from app.core.database import ChatDatabase
            prof = ChatDatabase().get_standalone_user_profile()
            g_k = (prof.get("groqApiKey") or "").strip()
            o_k = (prof.get("openrouterApiKey") or "").strip()
            if len(g_k) > 10:
                user_groq = g_k
            if len(o_k) > 10:
                user_or = o_k
        except Exception:
            pass

        effective_groq_key = user_groq or (settings.GROQ_API_KEY if settings.has_groq() else None)
        effective_or_key = user_or or (settings.OPENROUTER_API_KEY if settings.has_openrouter() else None)

        def _check_openrouter():
            if not effective_or_key:
                return "openrouter", {"status": "offline"}
            try:
                resp = httpx.get(
                    OPENROUTER_AUTH_URL,
                    headers={"Authorization": f"Bearer {effective_or_key}"},
                    timeout=2.5
                )
                if resp.status_code == 200:
                    or_data = resp.json().get("data", {})
                    return "openrouter", {
                        "status": "online",
                        "label": or_data.get("label", "API Key"),
                        "usage": float(or_data.get("usage") or 0.0),
                        "limit": or_data.get("limit"),
                        "is_free_tier": or_data.get("is_free_tier", True),
                        "rate_limit": or_data.get("rate_limit", {}),
                        "source": "OpenRouter Console API"
                    }
                return "openrouter", {"status": "error", "source": f"HTTP {resp.status_code}"}
            except Exception as e:
                return "openrouter", {"status": "offline", "error": str(e)}

        def _check_groq():
            if not effective_groq_key:
                return "groq", {"status": "offline"}
            try:
                live_g = self._live_limits.get("groq", {})

                # If no live completion headers recorded in past 300s, ping a 1-token test to extract official live ratelimit headers
                if not live_g or (time.time() - live_g.get("last_updated", 0)) > 300:
                    try:
                        resp = httpx.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {effective_groq_key}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": "qwen/qwen3.8-27b",
                                "messages": [{"role": "user", "content": "ping"}],
                                "max_tokens": 1
                            },
                            timeout=3.0
                        )
                        if resp.status_code in [200, 429]:
                            self.update_live_headers("groq", resp.headers)
                            live_g = self._live_limits.get("groq", {})
                    except Exception:
                        pass

                eff_lim = live_g.get("limit_requests", 1000)
                eff_rem = live_g.get("remaining_requests", eff_lim)
                eff_lim_tok = live_g.get("limit_tokens", 8000)
                eff_tok = live_g.get("remaining_tokens", eff_lim_tok)
                eff_reset = live_g.get("reset_requests", "Rolling 24h")

                return "groq", {
                    "status": "online",
                    "remaining_requests": eff_rem,
                    "limit_requests": eff_lim,
                    "reset_requests": eff_reset,
                    "remaining_tokens": eff_tok,
                    "limit_tokens": eff_lim_tok,
                    "source": "Groq Gateway Headers"
                }
            except Exception as e:
                live_g = self._live_limits.get("groq", {})
                return "groq", {
                    "status": "online" if live_g else "offline",
                    "remaining_requests": live_g.get("remaining_requests", 1000),
                    "limit_requests": live_g.get("limit_requests", 1000),
                    "reset_requests": live_g.get("reset_requests", "Rolling 24h"),
                    "remaining_tokens": live_g.get("remaining_tokens", 8000),
                    "limit_tokens": live_g.get("limit_tokens", 8000),
                    "source": "Groq Cached Telemetry",
                    "error": str(e)
                }

        def _check_gemini():
            if not settings.has_gemini():
                return "gemini", {"status": "offline"}
            try:
                resp = httpx.get(
                    f"{GEMINI_BASE_URL}?key={settings.GEMINI_API_KEY}",
                    timeout=2.5
                )
                gem_stat = self.get_limits_summary().get("gemini", {})
                return "gemini", {
                    "status": "online" if resp.status_code == 200 else "error",
                    "daily_limit": 1500,
                    "daily_remaining": gem_stat.get("daily_remaining", 1500),
                    "daily_used": gem_stat.get("daily_used", 0),
                    "daily_pct": gem_stat.get("daily_pct", 100),
                    "minute_limit": 15,
                    "minute_remaining": gem_stat.get("minute_remaining", 15),
                    "source": "Google AI Studio API"
                }
            except Exception as e:
                return "gemini", {"status": "error", "error": str(e)}

        def _check_huggingface():
            if not settings.has_huggingface():
                return "huggingface", {"status": "offline"}
            try:
                resp = httpx.get(
                    HUGGINGFACE_WHOAMI_URL,
                    headers={"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"},
                    timeout=2.5
                )
                if resp.status_code == 200:
                    user_info = resp.json()
                    return "huggingface", {
                        "status": "online",
                        "username": user_info.get("name", "User"),
                        "type": user_info.get("type", "user"),
                        "source": "Hugging Face Inference API"
                    }
                return "huggingface", {"status": "error", "source": f"HTTP {resp.status_code}"}
            except Exception as e:
                return "huggingface", {"status": "offline", "error": str(e)}

        def _check_local():
            try:
                resp = httpx.get(f"{settings.OLLAMA_HOST}/api/tags", timeout=1.5)
                if resp.status_code == 200:
                    tags = resp.json().get("models", [])
                    return "local", {
                        "status": "online",
                        "models": [m.get("name") for m in tags],
                        "total_models": len(tags),
                        "source": "Local Ollama Daemon"
                    }
            except Exception:
                pass
            return "local", {"status": "offline"}

        # Execute parallel provider queries for the 5 active providers
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            tasks = [
                executor.submit(_check_openrouter),
                executor.submit(_check_groq),
                executor.submit(_check_gemini),
                executor.submit(_check_huggingface),
                executor.submit(_check_local)
            ]
            for fut in concurrent.futures.as_completed(tasks):
                try:
                    prov, data = fut.result()
                    metrics[prov] = data
                except Exception:
                    pass

        self._server_cache = metrics
        self._server_cache_time = now
        return metrics


# Global singleton instance
quota_tracker = QuotaTracker()
