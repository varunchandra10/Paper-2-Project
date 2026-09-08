import re
from app.tools.base_tool import BaseTool
from app.retrieval.vector_db import PaperVectorDB
from app.retrieval.embeddings import generate_local_embedding


def _normalize_paper_id(p_id: str) -> str:
    if not p_id:
        return ""
    clean = re.sub(r'[^a-zA-Z0-9]', '', p_id).lower()
    return clean.replace("paper", "")


class VectorSearchTool(BaseTool):
    name = "vector_search"
    description = "Queries vector DB for specific RAG chunks matching the user search query."

    def execute(self, query: str, paper_id: str = "") -> str:
        if not query:
            return "No search query provided."
            
        vector_db = PaperVectorDB()
        query_vector = generate_local_embedding(query)
        candidates = vector_db.hybrid_search(query, query_vector, top_k=15)
        
        if not candidates:
            candidates = vector_db.keyword_search(query, top_k=15)

        if not candidates:
            return f"No matching paper chunks found for query '{query}'."

        if paper_id:
            norm_target = _normalize_paper_id(paper_id)
            filtered = [
                c for c in candidates
                if c.get("paper_id") == paper_id
                or _normalize_paper_id(c.get("paper_id", "")) == norm_target
                or (norm_target and norm_target in _normalize_paper_id(c.get("paper_id", "")))
                or (_normalize_paper_id(c.get("paper_id", "")) and _normalize_paper_id(c.get("paper_id", "")) in norm_target)
            ]
            paper_chunks = filtered[:3] if filtered else candidates[:3]
        else:
            paper_chunks = candidates[:3]
            
        if not paper_chunks:
            return f"No matching paper chunks found for query '{query}'."
            
        results = []
        for idx, chunk in enumerate(paper_chunks, 1):
            content = (chunk.get("content") or "").strip()
            if len(content) > 750:
                content = content[:750] + "..."
            results.append(
                f"[Chunk {idx} (Page {chunk.get('page')}, Section: {chunk.get('section')})]:\n{content}"
            )
        return "\n\n".join(results)
