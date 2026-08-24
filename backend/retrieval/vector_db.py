import os
import json
import psycopg2
import math
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector
from typing import List, Dict, Any
from schemas.canonical_paper import PaperDocument
from schemas.rag_schemas import PaperChunk

# Load environment variables from backend/.env
from dotenv import load_dotenv
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(backend_dir, ".env"))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")


class PaperVectorDB:
    """
    Manages vector storage and hybrid retrieval using PostgreSQL + pgvector.
    Falls back gracefully to local JSON cache storage if database is unreachable.
    """
    
    def __init__(self, db_url: str = DATABASE_URL):
        self.db_url = db_url
        self.fallback_file = os.path.join(backend_dir, "papers", "in_memory_vector_db.json")
        self.use_fallback = False
        try:
            conn = psycopg2.connect(self.db_url, connect_timeout=3)
            conn.close()
        except Exception:
            self.use_fallback = True
            print(f"[DB WARN] PostgreSQL database unreachable. Falling back to local JSON storage: {self.fallback_file}")

    def _get_connection(self):
        """Helper to establish database connection and register vector type."""
        conn = psycopg2.connect(self.db_url)
        register_vector(conn)
        return conn

    def _load_fallback_data(self) -> dict:
        """Loads data from local JSON database."""
        if os.path.exists(self.fallback_file):
            try:
                with open(self.fallback_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"papers": {}, "chunks": []}

    def _write_fallback_data(self, data: dict):
        """Writes data to local JSON database."""
        try:
            with open(self.fallback_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DB ERROR] Failed to save local fallback DB: {e}")

    def initialize_db(self):
        """
        Enables the pgvector extension and creates papers and paper_chunks database schemas.
        """
        if self.use_fallback:
            if not os.path.exists(self.fallback_file):
                self._write_fallback_data({"papers": {}, "chunks": []})
            print("[DB] Local JSON database initialized successfully (Fallback).")
            return

        conn = psycopg2.connect(self.db_url)
        try:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS papers (
                        paper_id TEXT PRIMARY KEY,
                        title TEXT,
                        authors TEXT,
                        abstract TEXT,
                        metadata_json JSONB
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS paper_chunks (
                        chunk_id TEXT PRIMARY KEY,
                        paper_id TEXT REFERENCES papers(paper_id) ON DELETE CASCADE,
                        content TEXT,
                        section TEXT,
                        subsection TEXT,
                        page INTEGER,
                        content_type TEXT,
                        source_id TEXT,
                        embedding VECTOR(768)
                    );
                """)
                cur.execute("ALTER TABLE papers ALTER COLUMN paper_id TYPE TEXT;")
                cur.execute("ALTER TABLE paper_chunks ALTER COLUMN chunk_id TYPE TEXT;")
                cur.execute("ALTER TABLE paper_chunks ALTER COLUMN paper_id TYPE TEXT;")
                cur.execute("ALTER TABLE paper_chunks ALTER COLUMN content_type TYPE TEXT;")
                cur.execute("ALTER TABLE paper_chunks ALTER COLUMN source_id TYPE TEXT;")
            conn.commit()
            print("[DB] Database initialized successfully (PostgreSQL + pgvector).")
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def insert_paper_document(self, doc: PaperDocument, chunks: List[PaperChunk], embeddings: List[List[float]]):
        """
        Inserts a PaperDocument and its corresponding PaperChunks + embeddings.
        """
        if self.use_fallback:
            db_data = self._load_fallback_data()
            db_data["papers"][doc.paper_id] = {
                "paper_id": doc.paper_id,
                "title": doc.metadata.title,
                "authors": ", ".join(doc.metadata.authors),
                "abstract": doc.metadata.abstract,
                "metadata_json": doc.metadata.model_dump()
            }
            # Remove old chunks
            db_data["chunks"] = [c for c in db_data["chunks"] if c["paper_id"] != doc.paper_id]
            # Save new chunks
            for chunk, vector in zip(chunks, embeddings):
                db_data["chunks"].append({
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
            self._write_fallback_data(db_data)
            print(f"[DB] Saved {len(chunks)} chunks with local vector lists for '{doc.paper_id}'.")
            return

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO papers (paper_id, title, authors, abstract, metadata_json)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (paper_id) DO UPDATE 
                    SET title = EXCLUDED.title,
                        authors = EXCLUDED.authors,
                        abstract = EXCLUDED.abstract,
                        metadata_json = EXCLUDED.metadata_json;
                    """,
                    (
                        doc.paper_id,
                        doc.metadata.title,
                        ", ".join(doc.metadata.authors),
                        doc.metadata.abstract,
                        json.dumps(doc.metadata.model_dump())
                    )
                )
                cur.execute("DELETE FROM paper_chunks WHERE paper_id = %s;", (doc.paper_id,))
                
                chunk_data = []
                for chunk, vector in zip(chunks, embeddings):
                    chunk_data.append((
                        chunk.chunk_id,
                        doc.paper_id,
                        chunk.content,
                        chunk.section,
                        chunk.subsection,
                        chunk.page,
                        chunk.content_type,
                        chunk.source_id,
                        vector
                    ))
                execute_values(
                    cur,
                    """
                    INSERT INTO paper_chunks (chunk_id, paper_id, content, section, subsection, page, content_type, source_id, embedding)
                    VALUES %s
                    """,
                    chunk_data
                )
            conn.commit()
            print(f"[DB] Saved {len(chunks)} chunks with vectors for '{doc.paper_id}'.")
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def semantic_search(
        self, 
        query_vector: List[float], 
        top_k: int = 5, 
        content_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs cosine similarity search.
        """
        if self.use_fallback:
            def dot_product(v1, v2):
                return sum(x*y for x, y in zip(v1, v2))
            def magnitude(v):
                return math.sqrt(sum(x*x for x in v))
            def cosine_similarity(v1, v2):
                mag1 = magnitude(v1)
                mag2 = magnitude(v2)
                if mag1 == 0 or mag2 == 0:
                    return 0.0
                return dot_product(v1, v2) / (mag1 * mag2)

            db_data = self._load_fallback_data()
            candidates = []
            for c in db_data.get("chunks", []):
                if content_types and c.get("content_type") not in content_types:
                    continue
                emb = c.get("embedding")
                similarity = cosine_similarity(query_vector, emb) if emb else 0.0
                candidates.append({
                    "chunk_id": c.get("chunk_id"),
                    "paper_id": c.get("paper_id"),
                    "content": c.get("content"),
                    "section": c.get("section"),
                    "subsection": c.get("subsection"),
                    "page": c.get("page"),
                    "content_type": c.get("content_type"),
                    "source_id": c.get("source_id"),
                    "similarity_score": similarity
                })
            candidates = sorted(candidates, key=lambda x: x["similarity_score"], reverse=True)
            return candidates[:top_k]

        conn = self._get_connection()
        results = []
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT chunk_id, paper_id, content, section, subsection, page, content_type, source_id,
                           (embedding <=> %s::vector) AS distance
                    FROM paper_chunks
                """
                params = [query_vector]
                if content_types:
                    query += " WHERE content_type = ANY(%s)"
                    params.append(content_types)
                query += " ORDER BY distance ASC LIMIT %s;"
                params.append(top_k)

                cur.execute(query, tuple(params))
                for row in cur.fetchall():
                    distance = row[8]
                    similarity = 1.0 - distance if distance is not None else 0.0
                    results.append({
                        "chunk_id": row[0],
                        "paper_id": row[1],
                        "content": row[2],
                        "section": row[3],
                        "subsection": row[4],
                        "page": row[5],
                        "content_type": row[6],
                        "source_id": row[7],
                        "similarity_score": similarity
                    })
            return results
        finally:
            conn.close()

    def keyword_search(
        self, 
        query_text: str, 
        top_k: int = 10, 
        content_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs text keyword search.
        """
        if self.use_fallback:
            db_data = self._load_fallback_data()
            query_terms = [t.lower() for t in query_text.split() if len(t) > 2]
            candidates = []
            for c in db_data.get("chunks", []):
                if content_types and c.get("content_type") not in content_types:
                    continue
                content_lower = c.get("content", "").lower()
                matches = sum(1 for term in query_terms if term in content_lower)
                if matches == 0 and query_terms:
                    continue
                candidates.append({
                    "chunk_id": c.get("chunk_id"),
                    "paper_id": c.get("paper_id"),
                    "content": c.get("content"),
                    "section": c.get("section"),
                    "subsection": c.get("subsection"),
                    "page": c.get("page"),
                    "content_type": c.get("content_type"),
                    "source_id": c.get("source_id"),
                    "keyword_score": float(matches)
                })
            candidates = sorted(candidates, key=lambda x: x["keyword_score"], reverse=True)
            return candidates[:top_k]

        conn = self._get_connection()
        results = []
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT chunk_id, paper_id, content, section, subsection, page, content_type, source_id,
                           ts_rank_cd(to_tsvector('english', content), plainto_tsquery('english', %s)) AS rank
                    FROM paper_chunks
                    WHERE to_tsvector('english', content) @@ plainto_tsquery('english', %s)
                """
                params = [query_text, query_text]
                if content_types:
                    query += " AND content_type = ANY(%s)"
                    params.append(content_types)
                query += " ORDER BY rank DESC LIMIT %s;"
                params.append(top_k)

                cur.execute(query, tuple(params))
                for row in cur.fetchall():
                    results.append({
                        "chunk_id": row[0],
                        "paper_id": row[1],
                        "content": row[2],
                        "section": row[3],
                        "subsection": row[4],
                        "page": row[5],
                        "content_type": row[6],
                        "source_id": row[7],
                        "keyword_score": float(row[8]) if row[8] is not None else 0.0
                    })
            return results
        finally:
            conn.close()

    def hybrid_search(
        self,
        query_text: str,
        query_vector: List[float],
        top_k: int = 5,
        content_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Combines semantic search and keyword search.
        """
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
