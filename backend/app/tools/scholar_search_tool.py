import urllib.request
import urllib.parse
import json
from app.tools.base_tool import BaseTool


class ScholarSearchTool(BaseTool):
    name = "search_scholar_literature"
    description = "Queries Semantic Scholar literature API for academic metadata and paper summaries."

    def execute(self, query: str) -> str:
        if not query:
            return "No literature query provided."
            
        clean_q = query[:80].strip()
        encoded = urllib.parse.quote(clean_q)
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded}&limit=1&fields=title,abstract,tldr,citationCount"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Synthexis/2.0 Research Platform"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                
            papers = data.get("data", [])
            if not papers:
                return f"No Semantic Scholar literature matches found for '{clean_q}'."
                
            p = papers[0]
            title = p.get("title", "Unknown")
            tldr = p.get("tldr", {}).get("text", "N/A") if isinstance(p.get("tldr"), dict) else "N/A"
            citations = p.get("citationCount", "N/A")
            
            return f"Scholar Paper: '{title}' | Citations: {citations}\nTL;DR: {tldr}"
        except Exception as e:
            return f"Scholar lookup notice: Bypassed academic search for '{clean_q}' ({str(e)})."
