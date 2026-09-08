import pytest
from unittest.mock import patch, MagicMock
from app.core.model_router import ModelRouter


@pytest.fixture
def router():
    """Provides a ModelRouter instance with mocked API keys."""
    r = ModelRouter()
    r.groq_api_key = "gsk_test_groq_key_1234567890"
    r.openrouter_api_key = "sk-or-test_openrouter_key_1234567890"
    return r


# ── Groq execution & failover sequence ────────────────────────────────────────

def test_model_router_groq_primary_success(router):
    """Verifies direct success with primary Groq provider."""
    with patch("app.core.model_router.groq_adapter.complete") as mock_groq, \
         patch("app.core.model_router.quota_tracker") as mock_quota:
        mock_groq.return_value = {"success": True, "content": "Transformer response"}
        mock_quota.is_provider_available.return_value = True

        content, model_info = router.generate("What is attention?", model_id="qwen3.8")
        assert content == "Transformer response"
        assert "Groq Cloud" in model_info
        mock_quota.record_usage.assert_called_with("groq", "qwen3.8")


def test_model_router_groq_429_failover_to_gemini(router):
    """Verifies that HTTP 429 on Groq seamlessly fails over to Gemini 2.0 Flash."""
    with patch("app.core.model_router.groq_adapter.complete") as mock_groq, \
         patch("app.core.model_router.settings") as mock_settings, \
         patch("httpx.post") as mock_http, \
         patch("app.core.model_router.quota_tracker") as mock_quota:
        
        # Groq returns 429
        mock_groq.return_value = {"success": False, "status_code": 429}
        mock_quota.is_provider_available.return_value = True
        mock_settings.has_gemini.return_value = True
        mock_settings.GEMINI_API_KEY = "test_gemini_key"

        # Gemini returns 200 with candidates
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Gemini fallback response"}]}}]
        }
        mock_http.return_value = mock_resp

        content, model_info = router.generate("What is attention?", model_id="groq")
        assert content == "Gemini fallback response"
        assert "Gemini 2.0 Flash (Auto-Failover)" in model_info


def test_model_router_groq_429_gemini_fails_failover_to_openrouter(router):
    """Verifies failover to OpenRouter when both Groq 429s and Gemini fails."""
    with patch("app.core.model_router.groq_adapter.complete") as mock_groq, \
         patch("app.core.model_router.settings") as mock_settings, \
         patch("app.core.model_router.openrouter_adapter.complete") as mock_or, \
         patch("httpx.post", side_effect=Exception("Gemini connection timeout")), \
         patch("app.core.model_router.quota_tracker") as mock_quota:
        
        mock_groq.return_value = {"success": False, "status_code": 429}
        mock_quota.is_provider_available.return_value = True
        mock_settings.has_gemini.return_value = True
        mock_settings.GEMINI_API_KEY = "test_gemini_key"

        mock_or.return_value = {"success": True, "content": "OpenRouter failover answer"}

        content, model_info = router.generate("Explain ResNet", model_id="groq")
        assert content == "OpenRouter failover answer"
        assert "Auto-Failover" in model_info


def test_model_router_groq_429_all_cloud_fail_returns_retry_message(router):
    """Verifies friendly retry notification when all cloud failover targets fail."""
    with patch("app.core.model_router.groq_adapter.complete") as mock_groq, \
         patch("app.core.model_router.settings") as mock_settings, \
         patch("app.core.model_router.openrouter_adapter.complete") as mock_or, \
         patch("httpx.post", side_effect=Exception("Network error")), \
         patch("app.core.model_router.quota_tracker") as mock_quota:
        
        mock_groq.return_value = {"success": False, "status_code": 429}
        mock_quota.is_provider_available.return_value = True
        mock_settings.has_gemini.return_value = True
        mock_settings.has_huggingface.return_value = False

        mock_or.return_value = {"success": False, "status_code": 429}

        content, model_info = router.generate("Hello", model_id="groq")
        assert "⚠️ Groq rate limit reached (HTTP 429)" in content
        assert "groq" in model_info


def test_model_router_no_groq_key_warning():
    """Verifies clear warning message when Groq is selected without any configured API key."""
    empty_router = ModelRouter()
    empty_router.groq_api_key = ""
    with patch("app.core.database.ChatDatabase.get_standalone_user_profile", return_value={}):
        content, model_info = empty_router.generate("Prompt", model_id="groq")
        assert "⚠️ Groq API key is not configured" in content


# ── OpenRouter execution ───────────────────────────────────────────────────────

def test_model_router_openrouter_success(router):
    """Verifies standard execution when OpenRouter model is explicitly requested."""
    with patch("app.core.model_router.openrouter_adapter.complete") as mock_or, \
         patch("app.core.model_router.quota_tracker") as mock_quota:
        mock_quota.is_provider_available.return_value = True
        mock_or.return_value = {"success": True, "content": "OpenRouter DeepSeek analysis"}

        content, model_info = router.generate("Explain R1", model_id="google/gemini-2.5-flash:free")
        assert content == "OpenRouter DeepSeek analysis"
        assert "OpenRouter" in model_info
        mock_quota.record_usage.assert_called_with("openrouter", "google/gemini-2.5-flash:free")


def test_model_router_openrouter_rate_limited(router):
    """Verifies warning message when OpenRouter returns HTTP 429."""
    with patch("app.core.model_router.openrouter_adapter.complete") as mock_or, \
         patch("app.core.model_router.quota_tracker") as mock_quota:
        mock_quota.is_provider_available.return_value = True
        mock_or.return_value = {"success": False, "status_code": 429}

        content, model_info = router.generate("Explain R1", model_id="google/gemini-2.5-flash:free")
        assert "⚠️ OpenRouter rate limit reached" in content


# ── Local Ollama execution & fallback ──────────────────────────────────────────

def test_model_router_local_ollama_success(router):
    """Verifies local execution when an Ollama local model is chosen."""
    with patch("app.core.model_router.ollama_adapter.complete") as mock_local, \
         patch("app.core.model_router.quota_tracker") as mock_quota:
        mock_local.return_value = {"success": True, "content": "Local Qwen execution"}

        content, model_info = router.generate("Run local inference", model_id="ollama:qwen")
        assert content == "Local Qwen execution"
        assert "Local Ollama" in model_info
        mock_quota.record_usage.assert_called_with("local", "ollama:qwen")


def test_model_router_local_offline_fallback_to_groq(router):
    """Verifies automatic fallback to Groq when local Ollama daemon is offline."""
    with patch("app.core.model_router.ollama_adapter.complete") as mock_local, \
         patch("app.core.model_router.groq_adapter.complete") as mock_groq, \
         patch("app.core.model_router.quota_tracker") as mock_quota:
        mock_local.return_value = {"success": False, "error": "Connection refused"}
        mock_quota.is_provider_available.return_value = True
        mock_groq.return_value = {"success": True, "content": "Groq fallback for offline local"}

        content, model_info = router.generate("Summarize paper", model_id="ollama:qwen")
        assert content == "Groq fallback for offline local"
        assert "Groq Cloud" in model_info
