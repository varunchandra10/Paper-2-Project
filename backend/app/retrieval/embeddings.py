import ollama
import math
from typing import List
from app.core.config import settings


def generate_local_embedding(text: str, model_name: str = "nomic-embed-text") -> List[float]:
    """Generates embedding vector for a given text snippet using Ollama or deterministic fallback."""
    if not text or not text.strip():
        return [0.0] * 768
        
    try:
        client = ollama.Client(host=settings.OLLAMA_HOST)
        res = client.embeddings(model=model_name, prompt=text[:1000])
        emb = res.get("embedding", [])
        if emb:
            return emb
    except Exception as e:
        pass
        
    # Fallback: Deterministic lightweight embedding vector (768d)
    vector = [0.0] * 768
    for idx, char in enumerate(text[:768]):
        vector[idx % 768] += (ord(char) / 255.0)
        
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [round(x / norm, 4) for x in vector]
