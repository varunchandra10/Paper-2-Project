"""
Embedding generation service with retry handling, model metadata tracking,
and explicit error propagation to prevent silent corruption of vector stores.
"""

import time
import math
import logging
from typing import List, Optional
import ollama
from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_EMBEDDING_DIM = 768
EMBEDDING_VERSION = "2.0.0"


class EmbeddingError(RuntimeError):
    """Raised when embedding vector generation fails and cannot be recovered."""
    pass


def generate_local_embedding(
    text: str,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    max_retries: int = 2,
    retry_delay: float = 0.5,
    raise_on_failure: bool = True
) -> List[float]:
    """
    Generates embedding vector for a given text snippet using Ollama.
    Retries transient errors and raises EmbeddingError on persistent failure
    to eliminate silent mathematical corruption from pseudo-embeddings.
    """
    if not text or not text.strip():
        return [0.0] * DEFAULT_EMBEDDING_DIM

    last_error: Optional[Exception] = None
    prompt_text = text[:2000]

    for attempt in range(max_retries + 1):
        try:
            client = ollama.Client(host=settings.OLLAMA_HOST)
            res = client.embeddings(model=model_name, prompt=prompt_text)
            emb = res.get("embedding", [])
            if emb:
                return emb
            raise ValueError(f"Empty embedding vector returned by provider for model '{model_name}'")
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(retry_delay * (2 ** attempt))
                continue

    error_msg = f"Embedding generation failed for model '{model_name}' after {max_retries + 1} attempts: {last_error}"
    logger.error(error_msg)

    if raise_on_failure:
        raise EmbeddingError(error_msg) from last_error

    # Explicit zero-vector returned ONLY if raise_on_failure is explicitly disabled
    return [0.0] * DEFAULT_EMBEDDING_DIM


_LOCAL_EMBEDDING_CACHE: dict = {}


def generate_local_embeddings_batch(
    texts: List[str],
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    max_retries: int = 2,
    raise_on_failure: bool = True
) -> List[List[float]]:
    """
    Generates embeddings for a batch of text chunks with chunk hash caching
    to avoid redundant vector computations on duplicate text segments.
    """
    import hashlib
    embeddings: List[List[float]] = []
    for idx, text in enumerate(texts):
        if not text or not text.strip():
            embeddings.append([0.0] * DEFAULT_EMBEDDING_DIM)
            continue

        cache_key = f"{model_name}:{hashlib.sha256(text.strip().encode('utf-8')).hexdigest()}"
        if cache_key in _LOCAL_EMBEDDING_CACHE:
            embeddings.append(_LOCAL_EMBEDDING_CACHE[cache_key])
            continue

        emb = generate_local_embedding(
            text,
            model_name=model_name,
            max_retries=max_retries,
            raise_on_failure=raise_on_failure
        )
        _LOCAL_EMBEDDING_CACHE[cache_key] = emb
        embeddings.append(emb)

    return embeddings


def get_embedding_metadata(model_name: str = DEFAULT_EMBEDDING_MODEL) -> dict:
    """Returns metadata about the active embedding configuration."""
    return {
        "model_name": model_name,
        "dimensions": DEFAULT_EMBEDDING_DIM,
        "version": EMBEDDING_VERSION,
        "provider": "ollama",
        "host": settings.OLLAMA_HOST
    }
