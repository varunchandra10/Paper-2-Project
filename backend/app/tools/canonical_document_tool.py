import os
import json
from app.tools.base_tool import BaseTool
from app.core.config import settings


class CanonicalDocumentTool(BaseTool):
    name = "get_canonical_document"
    description = "Retrieves the full parsed canonical document structure, section titles, abstract, references bibliography, tables, or equations of the active paper."

    def execute(self, paper_id: str, query_type: str = "full") -> str:
        """
        Retrieves canonical paper content based on query_type.
        query_type can be: 'full', 'abstract', 'sections', 'references', 'tables', 'equations'
        """
        if not paper_id:
            return "No active paper specified."

        json_path = os.path.join(settings.EXTRACTED_JSON_DIR, f"{paper_id}.json")
        if not os.path.exists(json_path):
            return f"No extraction records found for paper '{paper_id}'."

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            doc = data.get("canonical_document")
            if not doc:
                return f"No canonical document content cached in extraction records for '{paper_id}' yet."

            q_type = query_type.lower().strip()
            
            if q_type == "abstract":
                meta = doc.get("metadata", {})
                return f"Abstract for '{paper_id}':\n{meta.get('abstract', 'No abstract found.')}"
                
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
                    formatted.append(f"## {sec_title}\n{sec_content}")
                return "\n\n".join(formatted)

            else:
                # Default: return structural summary
                meta = doc.get("metadata", {})
                sections = doc.get("sections", [])
                refs = doc.get("references", [])
                tables = doc.get("tables", [])
                eqs = doc.get("equations", [])
                
                summary = (
                    f"Canonical Document Summary for '{paper_id}':\n"
                    f"Title: {meta.get('title', 'Unknown Title')}\n"
                    f"Authors: {', '.join(meta.get('authors', []))}\n"
                    f"Sections Count: {len(sections)}\n"
                    f"Tables Count: {len(tables)}\n"
                    f"Equations Count: {len(eqs)}\n"
                    f"References Bibliography Count: {len(refs)}\n\n"
                    f"Abstract:\n{meta.get('abstract', 'N/A')}\n"
                )
                return summary

        except Exception as e:
            return f"Error loading canonical document for '{paper_id}': {str(e)}"
