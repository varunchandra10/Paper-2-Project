import json
import urllib.request
import urllib.parse
import ollama
from app.core.config import settings
from app.schemas.paper import PaperMetadata


def fetch_scholar_metadata(title: str) -> dict:
    """Queries Semantic Scholar API for paper TL;DR and citation metrics."""
    if not title:
        return {}
    clean_q = title[:80].strip()
    encoded = urllib.parse.quote(clean_q)
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded}&limit=1&fields=title,abstract,tldr,citationCount"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Synthexis/2.0 Research Platform"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        papers = data.get("data", [])
        if papers:
            p = papers[0]
            tldr = p.get("tldr", {}).get("text", "") if isinstance(p.get("tldr"), dict) else ""
            return {"tldr": tldr, "citations": p.get("citationCount", 0)}
    except Exception:
        pass
    return {}


def run_ingestion_agent(raw_sections: dict, model_name: str = settings.DEFAULT_MODEL) -> PaperMetadata:
    """Extracts paper title, abstract, domain, and authors using Ollama with Semantic Scholar fallback."""
    text_sample = "\n".join([f"{k}:\n{v[:500]}" for k, v in list(raw_sections.items())[:3]])
    
    prompt = f"""Extract the following JSON metadata from this paper text:
{{
  "title": "String",
  "abstract": "String",
  "domain": "String"
}}

Paper snippet:
{text_sample[:1500]}
"""
    try:
        client = ollama.Client(host=settings.OLLAMA_HOST)
        res = client.generate(model=model_name, prompt=prompt, format="json")
        data = json.loads(res.get("response", "{}"))
        
        title = data.get("title") or "Untitled Paper"
        scholar = fetch_scholar_metadata(title)
        
        return PaperMetadata(
            title=title,
            abstract=data.get("abstract") or text_sample[:300],
            domain=data.get("domain") or "Deep Learning",
            scholar_tldr=scholar.get("tldr"),
            citations=scholar.get("citations")
        )
    except Exception as e:
        print(f"[INGESTION AGENT WARN] Ollama metadata extraction fallback ({e}).")
        first_key = list(raw_sections.keys())[0] if raw_sections else "Paper"
        scholar = fetch_scholar_metadata(first_key)
        return PaperMetadata(
            title=first_key,
            abstract=raw_sections.get(first_key, "")[:300],
            scholar_tldr=scholar.get("tldr"),
            citations=scholar.get("citations")
        )
