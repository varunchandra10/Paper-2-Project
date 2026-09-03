import httpx
from fastapi import APIRouter
from app.core.config import settings
from app.core.database import ChatDatabase

router = APIRouter(prefix="/models", tags=["Inference Models"])

@router.get("")
@router.get("/")
async def get_available_models():
    """
    Returns available LLM inference engines (Cloud APIs + User-configured Local Ollama models).
    """
    has_api_keys = settings.has_groq() or settings.has_openrouter()
    cloud_tag = "CLOUD" if has_api_keys else "CLOUD (API Key)"
    provider_str = "Groq Cloud" if settings.has_groq() else ("OpenRouter" if settings.has_openrouter() else "Configurable API")

    default_cloud_models = [
        {
            "id": "llama-3.3-70b",
            "name": "Llama 3.3 70B",
            "tag": cloud_tag,
            "description": f"Main reasoning & paper synthesis ({provider_str})",
            "icon_type": "brain"
        },
        {
            "id": "qwen-2.5-coder-32b",
            "name": "Qwen 2.5 Coder 32B",
            "tag": "CODE",
            "description": f"Code generation & repository synthesis ({provider_str})",
            "icon_type": "code"
        },
        {
            "id": "deepseek-r1",
            "name": "DeepSeek R1",
            "tag": "REASONING",
            "description": f"Chain-of-thought derivations ({provider_str})",
            "icon_type": "brain"
        },
        {
            "id": "gemini-2.0-flash",
            "name": "Gemini 2.0 Flash",
            "tag": "LONG CTX",
            "description": f"Fast document RAG ({provider_str})",
            "icon_type": "robot"
        }
    ]

    models = list(default_cloud_models)
    
    # Check user-configured Ollama Link from storage/history/user_profile.json
    db = ChatDatabase()
    profile = db.get_standalone_user_profile()
    ollama_link = (profile.get("ollamaLink") or "").strip()
    
    # Query local Ollama instance ONLY IF user provided a valid ollamaLink
    if ollama_link and (ollama_link.startswith("http://") or ollama_link.startswith("https://")):
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                resp = await client.get(f"{ollama_link}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    ollama_models = data.get("models", [])
                    for om in ollama_models:
                        model_name = om.get("name", "local-ollama")
                        models.append({
                            "id": model_name,
                            "name": model_name.capitalize(),
                            "tag": "LOCAL",
                            "description": f"Offline Ollama local model ({model_name})",
                            "icon_type": "cpu"
                        })
        except Exception as e:
            print(f"[MODELS WARN] Provided Ollama link '{ollama_link}' is not live/responding: {e}")

    return {
        "status": "success",
        "total": len(models),
        "api_keys_active": has_api_keys,
        "ollama_configured": bool(ollama_link),
        "models": models
    }
