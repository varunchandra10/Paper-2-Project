import pytest
from app.core.limits_dashboard import get_limits_json_payload, generate_limits_html_dashboard


def test_get_limits_json_payload_structure():
    """Verify get_limits_json_payload produces standardized fields and provider keys."""
    payload = get_limits_json_payload()
    assert isinstance(payload, dict)
    assert payload["status"] == "success"
    assert "timestamp" in payload
    assert isinstance(payload["timestamp"], int)
    
    # Check limits structure
    limits = payload.get("limits", {})
    assert isinstance(limits, dict)
    for provider in ["gemini", "huggingface", "groq", "openrouter", "local"]:
        assert provider in limits, f"Missing provider {provider} in limits summary"
        
    # Check server_metrics structure
    server_metrics = payload.get("server_metrics", {})
    assert isinstance(server_metrics, dict)


def test_generate_limits_html_dashboard_content():
    """Verify HTML dashboard renders clean markup with key provider cards and script."""
    html = generate_limits_html_dashboard()
    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html
    assert "Live Model Quotas & Rate Limits | RUEXIS AI" in html
    assert "Google Gemini 2.0 Flash" in html
    assert "Hugging Face Serverless Router" in html
    assert "Groq LPUs" in html
    assert "OpenRouter" in html
    assert "Local Ollama" in html
    assert "/api/v1/models/limits" in html
    assert "fetchLiveMetrics()" in html
