import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    PROJECT_NAME: str = "Synthexis AI Platform"
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
    CODES_DIR: str = os.path.join(STORAGE_DIR, "phase_8_codes")
    USER_PROFILE_FILE: str = os.path.join(STORAGE_DIR, "user_profile.json")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "synthexis_super_secret_jwt_key_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # External APIs & LLM Providers
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "").strip()
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "").strip()
    USER_REGISTRY_WEBHOOK: str = os.getenv("USER_REGISTRY_WEBHOOK", "").strip()

    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    GROBID_URL: str = os.getenv("GROBID_URL", "http://localhost:8070")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "qwen2.5-coder:1.5b")

    def has_groq(self) -> bool:
        return bool(self.GROQ_API_KEY and ("gsk_" in self.GROQ_API_KEY or len(self.GROQ_API_KEY) > 10))

    def has_openrouter(self) -> bool:
        return bool(self.OPENROUTER_API_KEY and ("sk-or-" in self.OPENROUTER_API_KEY or len(self.OPENROUTER_API_KEY) > 10))

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
