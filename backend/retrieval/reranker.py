import re
import ollama
from typing import List, Dict, Any
from .vector_db import PaperVectorDB


def rerank_candidates(
    query: str, 
    candidates: List[Dict[str, Any]], 
    model: str = "qwen2.5-coder:1.5b"
) -> List[Dict[str, Any]]:
    """
    Reranks a list of candidate chunks against the query using zero-shot relevance
    evaluations powered by the local qwen2.5-coder:1.5b LLM.
    """
    reranked = []
    
    for chunk in candidates:
        content = chunk["content"]
        
        system_instructions = (
            "You are an expert RAG search evaluator. Determine how relevant the following context chunk "
            "is to the user's query. Rate it on an integer scale from 0 to 5:\n"
            "- 0: Completely irrelevant.\n"
            "- 3: Mentions relevant keywords or concepts.\n"
            "- 5: Directly and explicitly answers the query.\n"
            "Respond with ONLY a single digit [0-5] and absolutely no other text."
        )
        
        prompt_content = f"Query: {query}\n\nContext Chunk:\n{content}\n\nScore:"
        
        try:
            # Query local Ollama service with temperature=0.0 for deterministic scoring
            response = ollama.generate(
                model=model,
                system=system_instructions,
                prompt=prompt_content,
                options={
                    "temperature": 0.0,
                    "num_predict": 5  # Limit tokens to prevent verbose LLM outputs
                }
            )
            
            output = response.get("response", "").strip()
            # Extract the first digit between 0 and 5 from response
            match = re.search(r'[0-5]', output)
            score = int(match.group(0)) if match else 0
            
        except Exception as e:
            print(f"⚠️ Reranker model call failed: {e}")
            score = 0
            
        record = chunk.copy()
        record["rerank_score"] = score
        reranked.append(record)
        
    return reranked


def generate_grounded_evidence(
    query: str,
    query_vector: List[float],
    top_k: int = 3,
    content_types: List[str] = None,
    db_url: str = None
) -> List[Dict[str, Any]]:
    """
    Retrieves candidate chunks using hybrid vector + keyword search, reranks them 
    using the local LLM, and compiles the final Grounded Evidence Package.
    """
    db = PaperVectorDB(db_url) if db_url else PaperVectorDB()
    
    # Retrieve more candidates than top_k to give the reranker options (e.g. top_k * 3)
    candidate_limit = max(top_k * 3, 10)
    
    # 1. Fetch RRF-fused hybrid search candidates
    candidates = db.hybrid_search(
        query_text=query,
        query_vector=query_vector,
        top_k=candidate_limit,
        content_types=content_types
    )
    
    if not candidates:
        return []
        
    # 2. Run LLM relevance scoring
    scored_candidates = rerank_candidates(query, candidates)
    
    # 3. Sort by:
    #    - Primary key: rerank_score (descending)
    #    - Secondary key: rrf_score (descending)
    sorted_evidence = sorted(
        scored_candidates, 
        key=lambda item: (item.get("rerank_score", 0), item.get("rrf_score", 0.0)), 
        reverse=True
    )
    
    # 4. Return top_k grounded evidence results
    return sorted_evidence[:top_k]
