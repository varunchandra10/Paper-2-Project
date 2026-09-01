from app.tools.base_tool import BaseTool
from app.retrieval.vector_db import PaperVectorDB
from app.retrieval.embeddings import generate_local_embedding


class VectorSearchTool(BaseTool):
    name = "vector_search"
    description = "Queries vector DB for specific RAG chunks matching the user search query."

    def execute(self, query: str, paper_id: str = "") -> str:
        if not query:
            return "No search query provided."
            
        vector_db = PaperVectorDB()
        query_vector = generate_local_embedding(query)
        candidates = vector_db.hybrid_search(query, query_vector, top_k=10)
        
        if paper_id:
            paper_chunks = [c for c in candidates if c.get("paper_id") == paper_id][:3]
        else:
            paper_chunks = candidates[:3]
            
        if not paper_chunks:
            return f"No matching paper chunks found for query '{query}'."
            
        results = []
        for idx, chunk in enumerate(paper_chunks, 1):
            results.append(
                f"[Chunk {idx} (Page {chunk.get('page')}, Section: {chunk.get('section')})]:\n{chunk.get('content')}"
            )
        return "\n\n".join(results)
