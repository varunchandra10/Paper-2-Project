import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from schemas.canonical_paper import PaperDocument
from schemas.rag_schemas import PaperChunk

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMBEDDINGS_DIR = os.path.join(backend_dir, "papers", "embeddings")
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)


class PaperVectorDB:
    """Manages local-first vector storage and high-performance hybrid retrieval

    using flat-file JSON caching and NumPy-based Cosine Similarity.
    """
    
    def __init__(self, db_url: str = None):
        self.embeddings_dir = EMBEDDINGS_DIR
        self.use_fallback = True

    def initialize_db(self):
        """Initializes local folders."""
        os.makedirs(self.embeddings_dir, exist_ok=True)
        print(f"[DB] Local-first flat vector cache initialized at: {self.embeddings_dir}")

    def insert_paper_document(self, doc: PaperDocument, chunks: List[PaperChunk], embeddings: List[List[float]]):
        """Saves a PaperDocument, its text chunks, and raw float vectors directly to a paper-specific JSON file."""
        file_path = os.path.join(self.embeddings_dir, f"{doc.paper_id}.json")
        
        serialized_chunks = []
        for chunk, vector in zip(chunks, embeddings):
            serialized_chunks.append({
                "chunk_id": chunk.chunk_id,
                "paper_id": doc.paper_id,
                "content": chunk.content,
                "section": chunk.section,
                "subsection": chunk.subsection,
                "page": chunk.page,
                "content_type": chunk.content_type,
                "source_id": chunk.source_id,
                "embedding": vector
            })
            
        data = {
            "metadata": {
                "paper_id": doc.paper_id,
                "title": doc.metadata.title,
                "authors": ", ".join(doc.metadata.authors),
                "abstract": doc.metadata.abstract,
                "metadata_json": doc.metadata.model_dump()
            },
            "chunks": serialized_chunks
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"[DB] Saved {len(chunks)} chunks with flat vectors to local cache: {file_path}")

    def semantic_search(
        self, 
        query_vector: List[float], 
        top_k: int = 5, 
        content_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Performs Cosine Similarity search over cached vectors using NumPy."""
        candidates = []
        
        if not os.path.exists(self.embeddings_dir):
            return candidates

        for filename in os.listdir(self.embeddings_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.embeddings_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        candidates.extend(data.get("chunks", []))
                except Exception:
                    pass

        if not candidates:
            return []

        if content_types:
            candidates = [c for c in candidates if c.get("content_type") in content_types]

        if not candidates:
            return []

        # Perform exact NumPy similarity search
        embeddings = np.array([c["embedding"] for c in candidates], dtype=np.float32)
        q_vec = np.array(query_vector, dtype=np.float32)

        # Vectorized cosine similarity calculations
        dot_products = np.dot(embeddings, q_vec)
        norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(q_vec)
        similarities = np.where(norms > 0, dot_products / norms, 0.0)

        results = []
        for idx, similarity in enumerate(similarities):
            c = candidates[idx]
            results.append({
                "chunk_id": c["chunk_id"],
                "paper_id": c["paper_id"],
                "content": c["content"],
                "section": c["section"],
                "subsection": c["subsection"],
                "page": c["page"],
                "content_type": c["content_type"],
                "source_id": c["source_id"],
                "similarity_score": float(similarity)
            })

        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

    def keyword_search(
        self, 
        query_text: str, 
        top_k: int = 10, 
        content_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Performs local case-insensitive term frequency keyword search."""
        candidates = []
        if not os.path.exists(self.embeddings_dir):
            return candidates

        for filename in os.listdir(self.embeddings_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.embeddings_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        candidates.extend(data.get("chunks", []))
                except Exception:
                    pass

        if not candidates:
            return []

        if content_types:
            candidates = [c for c in candidates if c.get("content_type") in content_types]

        query_terms = [t.lower() for t in query_text.split() if len(t) > 2]
        
        results = []
        for c in candidates:
            content_lower = c.get("content", "").lower()
            matches = sum(1 for term in query_terms if term in content_lower)
            if matches == 0 and query_terms:
                continue
            results.append({
                "chunk_id": c["chunk_id"],
                "paper_id": c["paper_id"],
                "content": c["content"],
                "section": c["section"],
                "subsection": c["subsection"],
                "page": c["page"],
                "content_type": c["content_type"],
                "source_id": c["source_id"],
                "keyword_score": float(matches)
            })

        results.sort(key=lambda x: x["keyword_score"], reverse=True)
        return results[:top_k]

    def hybrid_search(
        self,
        query_text: str,
        query_vector: List[float],
        top_k: int = 5,
        content_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Combines exact semantic vector search and keyword scores using Reciprocal Rank Fusion (RRF)."""
        search_limit = top_k * 2
        vector_results = self.semantic_search(query_vector, top_k=search_limit, content_types=content_types)
        keyword_results = self.keyword_search(query_text, top_k=search_limit, content_types=content_types)

        fused_scores = {}
        chunk_lookup = {}

        for rank, res in enumerate(vector_results, start=1):
            cid = res["chunk_id"]
            chunk_lookup[cid] = res
            fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (60.0 + rank))

        for rank, res in enumerate(keyword_results, start=1):
            cid = res["chunk_id"]
            if cid not in chunk_lookup:
                chunk_lookup[cid] = res
            fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (60.0 + rank))

        sorted_chunks = sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)
        final_results = []
        for cid, score in sorted_chunks[:top_k]:
            record = chunk_lookup[cid].copy()
            record.pop("similarity_score", None)
            record.pop("keyword_score", None)
            record["rrf_score"] = score
            final_results.append(record)

        return final_results

    def list_papers(self) -> List[Dict[str, Any]]:
        """Lists all ingested papers found in the embeddings cache directory."""
        papers = []
        if not os.path.exists(self.embeddings_dir):
            return papers

        for filename in os.listdir(self.embeddings_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.embeddings_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        papers.append(data.get("metadata"))
                except Exception:
                    pass
        return papers

    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single paper's metadata by ID."""
        file_path = os.path.join(self.embeddings_dir, f"{paper_id}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("metadata")
            except Exception:
                pass
        return None
