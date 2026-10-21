import re
from app.tools.base_tool import BaseTool
from app.retrieval.vector_db import PaperVectorDB
from app.retrieval.embeddings import generate_local_embedding


class VectorSearchTool(BaseTool):
    name = "vector_search"
    description = "Queries vector DB for specific RAG chunks matching the user search query, strictly isolated by paper_id."

    def execute(self, query: str, paper_id: str = "") -> str:
        if not query:
            return "No search query provided."

        vector_db = PaperVectorDB()
        query_vector = generate_local_embedding(query, raise_on_failure=False)
        target_paper_id = paper_id.strip() if paper_id else None

        candidates = vector_db.hybrid_search(
            query_text=query,
            query_vector=query_vector,
            top_k=5,
            paper_id=target_paper_id
        )

        if not candidates:
            candidates = vector_db.keyword_search(
                query_text=query,
                top_k=5,
                paper_id=target_paper_id
            )

        if not candidates:
            scope = f"in paper '{paper_id}'" if paper_id else "in vector database"
            return f"No matching paper chunks found {scope} for query '{query}'."

        results = []
        for idx, chunk in enumerate(candidates[:3], 1):
            content = (chunk.get("text") or chunk.get("content") or "").strip()
            if len(content) > 750:
                content = content[:750] + "..."
            results.append(
                f"[Chunk {idx} (Paper: {chunk.get('paper_id')}, Page {chunk.get('page')}, Section: {chunk.get('section')})]:\n{content}"
            )
        return "\n\n".join(results)
