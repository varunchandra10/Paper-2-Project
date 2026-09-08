import os
import re
import json
from app.tools.base_tool import BaseTool
from app.core.config import settings


class CanonicalDocumentTool(BaseTool):
    name = "get_canonical_document"
    description = "Retrieves the full parsed canonical document structure, section titles, abstract, references bibliography, tables, or equations of the active paper."

    def _find_json_path(self, paper_id: str) -> str:
        candidates = [paper_id]
        if paper_id.startswith("paper_"):
            candidates.append(paper_id[6:])
        else:
            candidates.append(f"paper_{paper_id}")
        slug = re.sub(r'[^a-zA-Z0-9]', '', paper_id).lower()
        candidates.extend([f"paper_{slug}", slug])

        for cid in candidates:
            p = os.path.join(settings.EXTRACTED_JSON_DIR, f"{cid}.json")
            if os.path.exists(p):
                return p
        
        # Fallback: if there is only 1 file in EXTRACTED_JSON_DIR, return it
        if os.path.exists(settings.EXTRACTED_JSON_DIR):
            files = [f for f in os.listdir(settings.EXTRACTED_JSON_DIR) if f.endswith(".json")]
            if len(files) == 1:
                return os.path.join(settings.EXTRACTED_JSON_DIR, files[0])
        return ""

    def execute(self, query: str = "full", paper_id: str = "", **kwargs) -> str:
        """
        Retrieves canonical paper content based on query_type.
        query_type can be: 'full', 'abstract', 'sections', 'references', 'tables', 'equations', 'summary'
        """
        target_paper_id = paper_id or kwargs.get("paper_id") or ""
        q_type = (query or kwargs.get("query_type") or "full").lower().strip()
        
        # If query parameter was actually passed as paper_id
        if not target_paper_id and ("paper" in q_type or "main" in q_type or "sgcd" in q_type):
            target_paper_id = q_type
            q_type = kwargs.get("query_type") or "full"

        json_path = self._find_json_path(target_paper_id) if target_paper_id else ""
        if not json_path and os.path.exists(settings.EXTRACTED_JSON_DIR):
            files = [f for f in os.listdir(settings.EXTRACTED_JSON_DIR) if f.endswith(".json")]
            if len(files) == 1:
                json_path = os.path.join(settings.EXTRACTED_JSON_DIR, files[0])
                target_paper_id = files[0].replace(".json", "")

        if not json_path or not os.path.exists(json_path):
            return f"No extraction records found for paper '{target_paper_id or 'unknown'}'."

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            doc = data.get("canonical_document") or data
            if not doc:
                return f"No canonical document content cached in extraction records for '{target_paper_id}' yet."

            if q_type == "abstract":
                meta = doc.get("metadata", {})
                return f"Abstract for '{target_paper_id}':\n{meta.get('abstract', 'No abstract found.')}"
                
            elif q_type == "references":
                refs = doc.get("references", [])
                if not refs:
                    return f"No bibliography references extracted for '{paper_id}'."
                formatted = [f"[{r.get('ref_id', idx+1)}] {r.get('citation_text', '')}" for idx, r in enumerate(refs)]
                return f"Bibliography References for '{paper_id}':\n" + "\n".join(formatted)
                
            elif q_type == "tables":
                tables = doc.get("tables", [])
                if not tables:
                    return f"No tables extracted for '{paper_id}'."
                formatted = [f"### Table {t.get('id', idx+1)}: {t.get('caption', '')}\n{t.get('content_markdown', '')}" for idx, t in enumerate(tables)]
                return f"Extracted Tables for '{paper_id}':\n" + "\n\n".join(formatted)

            elif q_type == "equations":
                eqs = doc.get("equations", [])
                if not eqs:
                    return f"No mathematical equations extracted for '{paper_id}'."
                formatted = [f"- {e.get('caption', 'Equation')}: {e.get('latex', '')} (Page {e.get('page', 1)})" for e in eqs]
                return f"Mathematical Equations for '{paper_id}':\n" + "\n".join(formatted)

            elif q_type == "sections":
                sections = doc.get("sections", [])
                if not sections:
                    return f"No sections structure found for '{paper_id}'."
                formatted = []
                for s in sections:
                    sec_title = s.get("title", "Section")
                    sec_content = s.get("content", "")
                    sub_parts = []
                    for sub_k, sub_v in s.get("subsections", {}).items():
                        sub_parts.append(f"### {sub_k}\n{sub_v}")
                    body = f"## {sec_title}\n{sec_content}\n" + "\n".join(sub_parts)
                    formatted.append(body.strip())
                return "\n\n".join(formatted)

            else:
                # Comprehensive structural and methodological summary
                meta = doc.get("metadata", {})
                sections = doc.get("sections", [])
                refs = doc.get("references", [])
                tables = doc.get("tables", [])
                eqs = doc.get("equations", [])
                
                # Build dense section highlights (prioritizing Method, Architecture, and Experiments)
                sec_highlights = []
                for s in sections:
                    stitle = s.get("title", "")
                    scontent = (s.get("content") or "").strip()
                    sub_names = list(s.get("subsections", {}).keys())
                    sub_desc = f" (Subsections: {', '.join(sub_names[:4])})" if sub_names else ""
                    
                    is_core = any(k in stitle.lower() for k in ["method", "architecture", "framework", "experiment", "model", "proposed"])
                    char_limit = 350 if is_core else 150
                    
                    if scontent:
                        sec_highlights.append(f"- **{stitle}**{sub_desc}: {scontent[:char_limit]}...")
                    elif sub_names:
                        sub_snippets = []
                        for sk, sv in list(s.get("subsections", {}).items())[:2]:
                            sub_snippets.append(f"  * **{sk}**: {sv[:200]}...")
                        sec_highlights.append(f"- **{stitle}**:\n" + "\n".join(sub_snippets))
                    else:
                        sec_highlights.append(f"- **{stitle}**{sub_desc}")

                highlights_text = "\n".join(sec_highlights) if sec_highlights else "Sections outline not yet indexed."

                summary = (
                    f"Canonical Document Summary for '{paper_id}':\n"
                    f"Title: {meta.get('title', 'Unknown Title')}\n"
                    f"Authors: {', '.join(meta.get('authors', []))}\n"
                    f"Primary Contribution: {meta.get('primary_contribution', 'N/A')}\n\n"
                    f"Abstract:\n{meta.get('abstract', 'N/A')}\n\n"
                    f"Extracted Sections & Methodological Overview:\n{highlights_text}\n"
                )
                return summary

        except Exception as e:
            return f"Error loading canonical document for '{paper_id}': {str(e)}"
