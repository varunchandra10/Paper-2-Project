import httpx
from fastapi import APIRouter
from app.core.config import settings
from app.core.database import ChatDatabase
from app.core.quota_tracker import quota_tracker
from app.core.limits_dashboard import get_limits_json_payload

router = APIRouter(prefix="/models", tags=["Inference Models"])


# [LEGACY GROQ 3.3 MODEL - PRESERVED & COMMENTED OUT]
# GROQ_MODELS = [
#     {
#         "id": "llama-3.3-70b-versatile",
#         "name": "Llama 3.3 70B",
#         "provider": "Groq",
#         "tag": "GROQ FREE",
#         "description": "Meta's flagship 70B model on high-speed LPU (128k context)",
#         "icon_type": "brain"
#     },
#     {
#         "id": "deepseek-r1-distill-llama-70b",
#         "name": "DeepSeek R1 (Groq)",
#         "provider": "Groq",
#         "tag": "GROQ REASON",
#         "description": "DeepSeek R1 reasoning on Groq LPU (128k context)",
#         "icon_type": "brain"
#     }
# ]
GROQ_MODELS = [
    {
        "id": "qwen/qwen3.8-27b",
        "name": "Qwen 3.8 27B",
        "provider": "Groq",
        "tag": "GROQ FREE",
        "description": "High-speed Qwen on Groq LPUs (ultra-fast reasoning & code)",
        "icon_type": "brain"
    },
    {
        "id": "openai/gpt-oss-120b",
        "name": "GPT-OSS 120B",
        "provider": "Groq",
        "tag": "GROQ FREE",
        "description": "Massive 120B open weights model running on Groq LPUs",
        "icon_type": "brain"
    }
    # [LEGACY GROQ COMPOUND - EXCLUDED TO AVOID EXTRA TOOL CHARGES / 250 RPD LIMIT]
    # Replaced by dedicated Google Scholar, arXiv, and Tavily academic search APIs.
    # {
    #     "id": "groq/compound",
    #     "name": "Compound (Reasoning)",
    #     "provider": "Groq",
    #     "tag": "GROQ REASON",
    #     "description": "Groq reasoning engine with step-by-step chain of thought",
    #     "icon_type": "brain"
    # }
]

# =============================================================================
# [LEGACY SAMBANOVA MODELS - PRESERVED & COMMENTED OUT]
# Retired due to payment method / card requirements (402 Payment Required).
# SAMBANOVA_MODELS = [
#     {
#         "id": "DeepSeek-V3.1",
#         "name": "DeepSeek V3.1",
#         "provider": "SambaNova",
#         "tag": "SAMBA FAST",
#         "description": "Flagship 671B MoE architecture on SambaNova SN40L accelerators",
#         "icon_type": "brain"
#     },
#     {
#         "id": "Meta-Llama-3.3-70B-Instruct",
#         "name": "Llama 3.3 70B",
#         "provider": "SambaNova",
#         "tag": "SAMBA CLOUD",
#         "description": "Meta 70B instruction-tuned model running on high-speed reconfigurable dataflow",
#         "icon_type": "brain"
#     }
# ]
# =============================================================================

# =============================================================================
# [HUGGING FACE MODELS - PRESERVED & COMMENTED OUT FROM FRONTEND]
# Hugging Face is dedicated strictly to the backend as Engine A in DualCodeEngine
# (Qwen/Qwen2.5-Coder-32B-Instruct) and is excluded from the frontend chat dropdown.
# HUGGINGFACE_MODELS = [
#     {
#         "id": "meta-llama/Llama-3.3-70B-Instruct",
#         "name": "Llama 3.3 70B (HF)",
#         "provider": "Hugging Face",
#         "tag": "HF CLOUD",
#         "description": "Meta 70B flagship on Hugging Face Serverless Inference Router",
#         "icon_type": "brain"
#     },
#     {
#         "id": "Qwen/Qwen2.5-Coder-32B-Instruct",
#         "name": "Qwen 2.5 Coder 32B (HF)",
#         "provider": "Hugging Face",
#         "tag": "HF CODE",
#         "description": "State-of-the-art coding and PyTorch synthesis specialist on Hugging Face",
#         "icon_type": "brain"
#     },
#     {
#         "id": "meta-llama/Llama-3.1-8B-Instruct",
#         "name": "Llama 3.1 8B (HF)",
#         "provider": "Hugging Face",
#         "tag": "HF FAST",
#         "description": "Fast instruction-following model on Hugging Face Serverless API",
#         "icon_type": "brain"
#     }
# ]
# =============================================================================

OPENROUTER_MODELS = [
    {
        "id": "google/gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "provider": "OpenRouter",
        "tag": "OR CLOUD",
        "description": "Google 1M+ context flagship multimodal model for large scientific PDF extraction & chat",
        "icon_type": "robot"
    },
    {
        "id": "deepseek/deepseek-r1:free",
        "name": "DeepSeek R1 (Free)",
        "provider": "OpenRouter",
        "tag": "OR FREE",
        "description": "Full 671B open-weights chain-of-thought reasoning model",
        "icon_type": "brain"
    }
    # [PRESERVED ALTERNATIVE OPENROUTER MODEL]
    # {
    #     "id": "google/gemma-4-31b-it:free",
    #     "name": "Gemma 4 31B (Free)",
    #     "provider": "OpenRouter",
    #     "tag": "OR FREE",
    #     "description": "Google high-capacity open model with 262k context for scientific reasoning",
    #     "icon_type": "robot"
    # }
]


@router.get("")
@router.get("/")
async def get_available_models():
    """
    Returns available LLM inference engines grouped into:
    1. Local Models (ONLY if physically installed on user system via Ollama)
    2. Groq Models (Free Tier)
    3. OpenRouter Models (Free Tier)
    """
    has_api_keys = settings.has_groq() or settings.has_openrouter()

    # 1. Probe Local Ollama for physically installed models
    local_models = []
    ollama_hosts = []
    if settings.OLLAMA_HOST:
        ollama_hosts.append(settings.OLLAMA_HOST)
    
    db = ChatDatabase()
    profile = db.get_standalone_user_profile()
    user_ollama_link = (profile.get("ollamaLink") or "").strip()
    if user_ollama_link and user_ollama_link not in ollama_hosts:
        ollama_hosts.append(user_ollama_link)
    
    if "http://localhost:11434" not in ollama_hosts:
        ollama_hosts.append("http://localhost:11434")

    ollama_online = False
    for host in ollama_hosts:
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                resp = await client.get(f"{host.rstrip('/')}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    ollama_list = data.get("models", [])
                    for om in ollama_list:
                        m_name = om.get("name", "local-ollama")
                        is_embed = "embed" in m_name.lower()
                        entry = {
                            "id": m_name,
                            "name": f"{m_name} (Local)",
                            "provider": "Local Ollama",
                            "tag": "LOCAL",
                            "description": f"Offline local Ollama model running on {host} (zero API costs)",
                            "icon_type": "cpu",
                            "is_local": True
                        }
                        if not is_embed:
                            local_models.insert(0, entry)
                        else:
                            local_models.append(entry)
                    if local_models:
                        ollama_online = True
                        break
        except Exception:
            pass

    # Frontend visible models: Groq (2 models) -> OpenRouter (2 models) -> Local Ollama (if available)
    # Hugging Face & Google Gemini are dedicated to the autonomous backend pipeline (Dual Code Engine & PDF Extraction)
    all_models = GROQ_MODELS + OPENROUTER_MODELS + local_models
    default_id = GROQ_MODELS[0]["id"] if GROQ_MODELS else (OPENROUTER_MODELS[0]["id"] if OPENROUTER_MODELS else (local_models[0]["id"] if local_models else ""))

    return {
        "status": "success",
        "total": len(all_models),
        "api_keys_active": has_api_keys or settings.has_huggingface(),
        "ollama_configured": ollama_online,
        "has_local_models": len(local_models) > 0,
        "default_model": default_id,
        "groups": {
            "groq": {
                "id": "groq",
                "title": "Groq Models (Free Tier)",
                "description": "Ultra-fast Groq LPU inference (2 models)",
                "available": settings.has_groq(),
                "models": GROQ_MODELS
            },
            "openrouter": {
                "id": "openrouter",
                "title": "OpenRouter Models (Free Tier)",
                "description": "OpenRouter Free community tier models (2 models)",
                "available": settings.has_openrouter(),
                "models": OPENROUTER_MODELS
            },
            # [HUGGING FACE DEDICATED TO BACKEND DUAL CODE ENGINE - EXCLUDED FROM FRONTEND]
            # "huggingface": {
            #     "id": "huggingface",
            #     "title": "Hugging Face Models",
            #     "available": settings.has_huggingface(),
            #     "models": HUGGINGFACE_MODELS
            # },
            "local": {
                "id": "local",
                "title": "Local Models (Ollama)",
                "description": "Runs on your hardware - zero API limits & complete privacy",
                "available": len(local_models) > 0,
                "models": local_models
            }
        },
        "models": all_models
    }


@router.get("/limits")
def get_model_limits():
    """Returns current rate limits and live console metrics for Groq, OpenRouter, and Local models."""
    return get_limits_json_payload()


@router.get("/dual-engine")
def get_dual_engine_status():
    """Returns availability and configuration of the dedicated Gemini + Hugging Face Dual Code Engine."""
    hf_active = settings.has_huggingface()
    gemini_active = settings.has_gemini()
    return {
        "status": "success",
        "dual_engine_ready": hf_active and gemini_active,
        "any_engine_ready": hf_active or gemini_active,
        "engines": {
            "huggingface": {
                "configured": hf_active,
                "model": "Qwen/Qwen2.5-Coder-32B-Instruct",
                "role": "High-Precision PyTorch Code Synthesis"
            },
            "gemini": {
                "configured": gemini_active,
                "model": settings.GEMINI_MODEL,
                "role": "Deep Context & Paper Nuance Synthesis"
            }
        }
    }

