import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/models", tags=["Inference Models"])

DEFAULT_CLOUD_MODELS = [
    {
        "id": "llama-3.3-70b",
        "name": "Llama 3.3 70B",
        "tag": "CLOUD",
        "description": "Main reasoning & paper Q&A synthesis (Groq / OpenRouter)",
        "icon_type": "brain"
    },
    {
        "id": "qwen-2.5-coder-32b",
        "name": "Qwen 2.5 Coder 32B",
        "tag": "CODE",
        "description": "Code generation & repository module synthesis",
        "icon_type": "code"
    },
    {
        "id": "deepseek-r1",
        "name": "DeepSeek R1",
        "tag": "REASONING",
        "description": "Deep mathematical derivations & verification",
        "icon_type": "brain"
    },
    {
        "id": "gemini-2.0-flash",
        "name": "Gemini 2.0 Flash",
        "tag": "LONG CTX",
        "description": "Long-document RAG & fast paper processing",
        "icon_type": "robot"
    }
]

@router.get("")
@router.get("/")
async def get_available_models():
    """
    Returns available LLM inference engines (Cloud + Local Ollama models).
    """
    models = list(DEFAULT_CLOUD_MODELS)
    
    # Query local Ollama instance for dynamically installed local models
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get("http://localhost:11434/api/tags")
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
    except Exception:
        # Fallback local entry if Ollama is not actively responding
        models.append({
            "id": "qwen2.5-coder:1.5b",
            "name": "Qwen 2.5 Coder 1.5B",
            "tag": "LOCAL",
            "description": "Offline Ollama local fallback engine",
            "icon_type": "cpu"
        })

    return {
        "status": "success",
        "total": len(models),
        "models": models
    }
