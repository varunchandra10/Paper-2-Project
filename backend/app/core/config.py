import os
from typing import List


class Settings:
    PROJECT_NAME: str = "Synthexis AI Platform"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    # Base directories
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    STORAGE_DIR: str = os.path.join(BASE_DIR, "storage")
    PAPERS_DIR: str = os.path.join(STORAGE_DIR, "papers")
    HISTORY_DIR: str = os.path.join(STORAGE_DIR, "history")
    EXTRACTED_JSON_DIR: str = os.path.join(HISTORY_DIR, "extracted_json")
    TRACES_DIR: str = os.path.join(HISTORY_DIR, "traces")
    CONVERSATIONS_DIR: str = os.path.join(HISTORY_DIR, "conversations")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "synthexis_super_secret_jwt_key_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # External APIs & LLM Providers
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    GROBID_URL: str = os.getenv("GROBID_URL", "http://localhost:8070")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "qwen2.5-coder:1.5b")

    def ensure_directories(self):
        """Ensures all persistent storage directories exist."""
        for d in [self.STORAGE_DIR, self.PAPERS_DIR, self.HISTORY_DIR, self.EXTRACTED_JSON_DIR, self.TRACES_DIR, self.CONVERSATIONS_DIR]:
            os.makedirs(d, exist_ok=True)


settings = Settings()
settings.ensure_directories()
