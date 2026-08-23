import ollama
from typing import List, Dict, Any
from schemas.rag_schemas import PaperChunk


def generate_local_embedding(text: str, model: str = "nomic-embed-text") -> List[float]:
    """
    Generates a 768-dimensional text embedding locally using the Ollama HTTP API.
    """
    if not text.strip():
        # Return empty list or zeros for blank text to prevent API errors
        return [0.0] * 768
        
    response = ollama.embeddings(model=model, prompt=text)
    return response.get("embedding", [])


def batch_embed_chunks(chunks: List[PaperChunk], model: str = "nomic-embed-text") -> List[Dict[str, Any]]:
    """
    Sequentially embeds a list of PaperChunks, attaching the resulting float vector 
    to each dictionary representation.
    """
    payloads = []
    for idx, chunk in enumerate(chunks):
        vector = generate_local_embedding(chunk.content, model=model)
        serialized = chunk.model_dump()
        serialized["embedding"] = vector
        payloads.append(serialized)
    return payloads
