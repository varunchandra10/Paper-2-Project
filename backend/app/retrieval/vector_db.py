import os
import json
import hashlib
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.schemas.paper import PaperDocument
from app.retrieval.chunker import PaperChunk
from app.retrieval.embeddings import get_embedding_metadata

logger = logging.getLogger(__name__)

EMBEDDINGS_DIR = getattr(settings, "RAG_EMBEDDINGS_DIR", os.path.join(settings.STORAGE_DIR, "rag_based"))
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)


class PaperVectorDB:
    """Manages local-first vector storage and high-performance hybrid retrieval
    using flat-file JSON caching and NumPy-based Cosine Similarity with strict
    per-paper data isolation to prevent cross-paper contamination.
    """

    def __init__(self, db_url: str = None):
        self.embeddings_dir = EMBEDDINGS_DIR
        self.use_fallback = True

    def initialize_db(self):
        """Initializes local storage directory."""
        os.makedirs(self.embeddings_dir, exist_ok=True)

    def insert_paper_document(
        self,
        doc: PaperDocument,
        chunks: List[PaperChunk],
        embeddings: List[List[float]]
    ) -> Dict[str, Any]:
        """
        Saves a PaperDocument, its text chunks, and float vectors directly to a paper-specific JSON file.
        Deduplicates chunks via content hashing and records embedding metadata.
        """
        file_path = os.path.join(self.embeddings_dir, f"{doc.paper_id}.json")

        seen_hashes = set()
        serialized_chunks = []
        deduplicated_count = 0

        for chunk, vector in zip(chunks, embeddings):
            content_str = chunk.content.strip() if chunk.content else ""
            if not content_str:
                continue

            content_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
            if content_hash in seen_hashes:
                deduplicated_count += 1
                continue
            seen_hashes.add(content_hash)

            serialized_chunks.append({
                "chunk_id": chunk.chunk_id,
                "paper_id": doc.paper_id,
                "content": chunk.content,
                "text": chunk.content,
                "section": getattr(chunk, "section", "main"),
                "subsection": getattr(chunk, "subsection", None),
                "page": getattr(chunk, "page", 1),
                "content_type": getattr(chunk, "content_type", "text"),
                "source_id": getattr(chunk, "source_id", doc.paper_id),
                "embedding": vector,
                "content_hash": content_hash
            })

        data = {
            "metadata": {
                "paper_id": doc.paper_id,
                "title": getattr(doc.metadata, "title", doc.paper_id),
                "authors": ", ".join(getattr(doc.metadata, "authors", [])) if isinstance(getattr(doc.metadata, "authors", []), list) else str(getattr(doc.metadata, "authors", "")),
                "abstract": getattr(doc.metadata, "abstract", ""),
                "metadata_json": doc.metadata.model_dump() if hasattr(doc.metadata, "model_dump") else {},
                "chunk_count": len(serialized_chunks),
                "deduplicated_count": deduplicated_count,
                "embedding_metadata": get_embedding_metadata()
            },
            "chunks": serialized_chunks
        }

        # Atomically write to avoid partial file states
        temp_path = f"{file_path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, file_path)

        logger.info(f"[DB] Saved {len(serialized_chunks)} chunks (deduplicated {deduplicated_count}) to {file_path}")
        return {
            "paper_id": doc.paper_id,
            "chunks_stored": len(serialized_chunks),
            "deduplicated": deduplicated_count,
            "file_path": file_path
        }

    def index_paper_chunks(self, chunks: List[PaperChunk]):
        """Helper generating embeddings and inserting all chunks for a paper."""
        from app.retrieval.embeddings import generate_local_embeddings_batch
        if not chunks:
            return
        paper_id = chunks[0].paper_id
        texts = [c.content for c in chunks]
        embeddings = generate_local_embeddings_batch(texts)

        class MetaObj:
            title = paper_id
            authors = []
            abstract = ""
            def model_dump(self): return {}

        class DocObj:
            pass

        doc = DocObj()
        doc.paper_id = paper_id
        doc.metadata = MetaObj()
        return self.insert_paper_document(doc, chunks, embeddings)

    def delete_paper(self, paper_id: str) -> bool:
        """Removes a paper's vector file and cached chunks from storage."""
        file_path = os.path.join(self.embeddings_dir, f"{paper_id}.json")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"[DB] Deleted vector index for paper '{paper_id}'")
                return True
            except Exception as e:
                logger.error(f"[DB ERROR] Failed to delete vector index for '{paper_id}': {e}")
                return False
        return False

    def _get_candidates(self, paper_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Internal candidate loader enforcing strict paper-level isolation.
        When paper_id is provided, loads ONLY that paper's JSON file.
        """
        candidates: List[Dict[str, Any]] = []
        if not os.path.exists(self.embeddings_dir):
            return candidates

        if paper_id:
            # STRICT ISOLATION: Read exclusively the target paper file
            file_path = os.path.join(self.embeddings_dir, f"{paper_id}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        candidates = data.get("chunks", [])
                except Exception as e:
                    logger.warning(f"[DB] Failed to load vector file for '{paper_id}': {e}")
            return candidates

        # Multi-paper scan ONLY if paper_id is explicitly omitted
        for filename in os.listdir(self.embeddings_dir):
            if filename.endswith(".json") and not filename.endswith(".tmp"):
                file_path = os.path.join(self.embeddings_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        candidates.extend(data.get("chunks", []))
                except Exception:
                    pass
        return candidates

    def semantic_search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        paper_id: Optional[str] = None,
        content_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs Cosine Similarity search over cached vectors using NumPy.
        Guarantees zero cross-paper contamination when paper_id is supplied.
        """
        candidates = self._get_candidates(paper_id=paper_id)
        if not candidates:
            return []

        if content_types:
            candidates = [c for c in candidates if c.get("content_type") in content_types]

        if not candidates:
            return []

        embeddings = np.array([c["embedding"] for c in candidates if "embedding" in c], dtype=np.float32)
        if len(embeddings) == 0:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)

        # Vectorized cosine similarity calculations
        dot_products = np.dot(embeddings, q_vec)
        norms = np.linalg.norm(embeddings, axis=1) * (np.linalg.norm(q_vec) + 1e-9)
        similarities = np.where(norms > 0, dot_products / norms, 0.0)

        results = []
        for idx, similarity in enumerate(similarities):
            c = candidates[idx]
            sim_val = float(similarity)
            results.append({
                "chunk_id": c.get("chunk_id", f"chk_{idx}"),
                "paper_id": c.get("paper_id", paper_id or ""),
                "text": c.get("content", ""),
                "content": c.get("content", ""),
                "section": c.get("section", "main"),
                "subsection": c.get("subsection"),
                "page": c.get("page", 1),
                "content_type": c.get("content_type", "text"),
                "source_id": c.get("source_id", ""),
                "score": sim_val,
                "similarity_score": sim_val
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def keyword_search(
        self,
        query_text: str,
        top_k: int = 10,
        paper_id: Optional[str] = None,
        content_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs local case-insensitive term frequency keyword search.
        Guarantees zero cross-paper contamination when paper_id is supplied.
        """
        candidates = self._get_candidates(paper_id=paper_id)
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
            score_val = float(matches)
            results.append({
                "chunk_id": c.get("chunk_id", ""),
                "paper_id": c.get("paper_id", paper_id or ""),
                "text": c.get("content", ""),
                "content": c.get("content", ""),
                "section": c.get("section", "main"),
                "subsection": c.get("subsection"),
                "page": c.get("page", 1),
                "content_type": c.get("content_type", "text"),
                "source_id": c.get("source_id", ""),
                "score": score_val,
                "keyword_score": score_val
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def hybrid_search(
        self,
        query_text: str,
        query_vector: List[float],
        top_k: int = 5,
        paper_id: Optional[str] = None,
        content_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Combines exact semantic vector search and keyword scores using Reciprocal Rank Fusion (RRF).
        Strictly isolates retrieval to paper_id when provided.
        """
        search_limit = top_k * 2
        vector_results = self.semantic_search(query_vector, top_k=search_limit, paper_id=paper_id, content_types=content_types)
        keyword_results = self.keyword_search(query_text, top_k=search_limit, paper_id=paper_id, content_types=content_types)

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
            record["score"] = float(score)
            record["rrf_score"] = float(score)
            final_results.append(record)

        return final_results

    def list_papers(self) -> List[Dict[str, Any]]:
        """Lists all ingested papers found in the embeddings cache directory."""
        papers = []
        if not os.path.exists(self.embeddings_dir):
            return papers

        for filename in os.listdir(self.embeddings_dir):
            if filename.endswith(".json") and not filename.endswith(".tmp"):
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
