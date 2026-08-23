import os
import json
import psycopg2
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
    Manages vector storage and hybrid retrieval using PostgreSQL and the pgvector extension.
    """
    
    def __init__(self, db_url: str = DATABASE_URL):
        self.db_url = db_url

    def _get_connection(self):
        """Helper to establish database connection and register vector type."""
        conn = psycopg2.connect(self.db_url)
        # Register pgvector type handlers with psycopg2
        register_vector(conn)
        return conn

    def initialize_db(self):
        """
        Enables the pgvector extension and creates papers and paper_chunks database schemas.
        """
        conn = psycopg2.connect(self.db_url)
        try:
            with conn.cursor() as cur:
                # 1. Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # 2. Create papers table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS papers (
                        paper_id TEXT PRIMARY KEY,
                        title TEXT,
                        authors TEXT,
                        abstract TEXT,
                        metadata_json JSONB
                    );
                """)
                
                # 3. Create paper_chunks table with 768-dim vector column
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
                
                # 4. Legacy schema migrations: alter column types to TEXT to avoid character varying errors
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
        Executes atomically inside a transaction block.
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # 1. Insert/Replace paper metadata
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

                # Delete existing chunks for this paper before re-inserting
                cur.execute("DELETE FROM paper_chunks WHERE paper_id = %s;", (doc.paper_id,))

                # 2. Batch insert chunks + embeddings
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

                # Efficient batch insert using execute_values
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
        Performs cosine distance vector similarity query using the pgvector <=> operator.
        Returns the top_k closest chunks with their similarity score (1 - distance).
        """
        conn = self._get_connection()
        results = []
        try:
            with conn.cursor() as cur:
                # Base query selecting columns and calculating cosine distance
                query = """
                    SELECT chunk_id, paper_id, content, section, subsection, page, content_type, source_id,
                           (embedding <=> %s::vector) AS distance
                    FROM paper_chunks
                """
                params = [query_vector]

                # Optional content types filtering
                if content_types:
                    query += " WHERE content_type = ANY(%s)"
                    params.append(content_types)

                query += " ORDER BY distance ASC LIMIT %s;"
                params.append(top_k)

                cur.execute(query, tuple(params))
                
                # Fetch and format results
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
        Performs a full-text search against paper chunks using PostgreSQL FTS.
        """
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
        Combines semantic vector search and keyword FTS results using Reciprocal Rank Fusion (RRF).
        RRF Score: 1 / (60 + rank_vector) + 1 / (60 + rank_keyword)
        """
        search_limit = top_k * 2
        
        vector_results = self.semantic_search(query_vector, top_k=search_limit, content_types=content_types)
        keyword_results = self.keyword_search(query_text, top_k=search_limit, content_types=content_types)

        fused_scores = {}
        chunk_lookup = {}

        # 1. Score Vector Results
        for rank, res in enumerate(vector_results, start=1):
            cid = res["chunk_id"]
            chunk_lookup[cid] = res
            fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (60.0 + rank))

        # 2. Score Keyword Results
        for rank, res in enumerate(keyword_results, start=1):
            cid = res["chunk_id"]
            if cid not in chunk_lookup:
                chunk_lookup[cid] = res
            fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (60.0 + rank))

        # 3. Sort by combined RRF score descending
        sorted_chunks = sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)

        # 4. Compile final list of top_k results
        final_results = []
        for cid, score in sorted_chunks[:top_k]:
            record = chunk_lookup[cid].copy()
            record.pop("similarity_score", None)
            record.pop("keyword_score", None)
            record["rrf_score"] = score
            final_results.append(record)

        return final_results
