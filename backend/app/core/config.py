import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    PROJECT_NAME: str = "RUEXIS AI Platform"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    # Base directories
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    STORAGE_DIR: str = os.path.join(BASE_DIR, "storage")
    PAPERS_DIR: str = os.path.join(STORAGE_DIR, "papers")
    HISTORY_DIR: str = os.path.join(STORAGE_DIR, "history")
    REPORTS_DIR: str = os.path.join(STORAGE_DIR, "reports")
    EXTRACTED_JSON_DIR: str = os.path.join(STORAGE_DIR, "extracted_json")
    KNOWLEDGE_GRAPHS_DIR: str = os.path.join(STORAGE_DIR, "knowledge_graphs")
    RAG_EMBEDDINGS_DIR: str = os.path.join(STORAGE_DIR, "rag_embeddings")
    TRACES_DIR: str = os.path.join(STORAGE_DIR, "traces")
    CONVERSATIONS_DIR: str = os.path.join(STORAGE_DIR, "conversations")
    CODES_DIR: str = os.path.join(STORAGE_DIR, "codes")
    USER_PROFILE_FILE: str = os.path.join(STORAGE_DIR, "user_profile.json")

    # Security
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    @property
    def SECRET_KEY(self) -> str:
        key = os.getenv("SECRET_KEY", "")
        if not key or key == "ruexis_super_secret_jwt_key_2026":
            self._reload_env()
            key = os.getenv("SECRET_KEY", "")
        if not key or key == "ruexis_super_secret_jwt_key_2026":
            raise RuntimeError(
                "SECRET_KEY is not set in .env. Generate one with: "
                "python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return key

    # External APIs & LLM Providers
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "").strip()
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "").strip()
    USER_REGISTRY_WEBHOOK: str = os.getenv("USER_REGISTRY_WEBHOOK", "").strip()
    EXTRACTION_PROVIDER: str = os.getenv("EXTRACTION_PROVIDER", "gemini").strip().lower()  # 'gemini' or 'openrouter'

    def _reload_env(self):
        """Reloads .env file from disk dynamically."""
        env_file = os.path.join(self.BASE_DIR, ".env")
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)

    @property
    def GEMINI_API_KEY(self) -> str:
        k = os.getenv("GEMINI_API_KEY") or os.getenv("gemini api") or ""
        if not k or len(k) < 10:
            self._reload_env()
            k = os.getenv("GEMINI_API_KEY") or os.getenv("gemini api") or ""
        return k.strip()

    # [LEGACY CEREBRAS CONFIG - PRESERVED & COMMENTED OUT]
    # @property
    # def CEREBRAS_API_KEY(self) -> str:
    #     k = os.getenv("CEREBRAS_API_KEY") or os.getenv("cerebras") or ""
    #     if not k or len(k) < 10:
    #         self._reload_env()
    #         k = os.getenv("CEREBRAS_API_KEY") or os.getenv("cerebras") or ""
    #     return k.strip()
    # CEREBRAS_MODEL: str = os.getenv("CEREBRAS_MODEL", "llama-3.3-70b").strip()
    CEREBRAS_API_KEY: str = ""
    CEREBRAS_MODEL: str = ""

    @property
    def SAMBANOVA_API_KEY(self) -> str:
        k = os.getenv("SAMBANOVA_API_KEY") or os.getenv("sambanova") or ""
        if not k or len(k) < 10:
            self._reload_env()
            k = os.getenv("SAMBANOVA_API_KEY") or os.getenv("sambanova") or ""
        return k.strip()

    # Dedicated Code Generation Engines
    # [LEGACY GEMINI_MODEL - PRESERVED & COMMENTED OUT]
    # GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    SAMBANOVA_MODEL: str = os.getenv("SAMBANOVA_MODEL", "Meta-Llama-3.3-70B-Instruct").strip()

    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    GROBID_URL: str = os.getenv("GROBID_URL", "http://localhost:8070")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile")

    def has_groq(self) -> bool:
        return bool(self.GROQ_API_KEY and ("gsk_" in self.GROQ_API_KEY or len(self.GROQ_API_KEY) > 10))

    def has_openrouter(self) -> bool:
        return bool(self.OPENROUTER_API_KEY and ("sk-or-" in self.OPENROUTER_API_KEY or len(self.OPENROUTER_API_KEY) > 10))

    def has_gemini(self) -> bool:
        key = self.GEMINI_API_KEY
        return bool(key and len(key) > 10 and "your_" not in key.lower())

    def has_cerebras(self) -> bool:
        # [LEGACY CEREBRAS CHECK - PRESERVED & COMMENTED OUT]
        # key = self.CEREBRAS_API_KEY
        # return bool(key and ("csk-" in key or len(key) > 10))
        return False

    @property
    def HUGGINGFACE_API_KEY(self) -> str:
        k = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN") or ""
        if not k or len(k) < 10:
            self._reload_env()
            k = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN") or ""
        return k.strip()

    def has_sambanova(self) -> bool:
        # [LEGACY SAMBANOVA CHECK - PRESERVED & COMMENTED OUT]
        # key = self.SAMBANOVA_API_KEY
        # return bool(key and len(key) > 10 and "your_" not in key.lower())
        return False

    def has_huggingface(self) -> bool:
        key = self.HUGGINGFACE_API_KEY
        return bool(key and ("hf_" in key or len(key) > 10))

    def has_tavily(self) -> bool:
        return bool(self.TAVILY_API_KEY and "your_" not in self.TAVILY_API_KEY.lower())

    def ensure_directories(self):
        """Ensures all persistent storage directories exist."""
        for d in [self.STORAGE_DIR, self.PAPERS_DIR, self.HISTORY_DIR, self.REPORTS_DIR,
                  self.EXTRACTED_JSON_DIR, self.KNOWLEDGE_GRAPHS_DIR, self.RAG_EMBEDDINGS_DIR,
                  self.TRACES_DIR, self.CONVERSATIONS_DIR, self.CODES_DIR]:
            os.makedirs(d, exist_ok=True)


settings = Settings()
settings.ensure_directories()
_ = settings.SECRET_KEY
