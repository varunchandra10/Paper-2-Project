import os
import re
import json
from app.tools.base_tool import BaseTool
from app.core.config import settings


class HyperparameterTool(BaseTool):
    name = "get_hyperparameters"
    description = "Retrieves extracted and user-approved hyperparameters for a given paper."

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
        
        # Fallback if only 1 file in directory
        if os.path.exists(settings.EXTRACTED_JSON_DIR):
            files = [f for f in os.listdir(settings.EXTRACTED_JSON_DIR) if f.endswith(".json")]
            if len(files) == 1:
                return os.path.join(settings.EXTRACTED_JSON_DIR, files[0])
        return ""

    def execute(self, query: str = "", paper_id: str = "", **kwargs) -> str:
        target_paper_id = paper_id or kwargs.get("paper_id") or query or ""
        if not target_paper_id:
            return "No paper ID specified."
            
        json_path = self._find_json_path(target_paper_id)
        if not json_path or not os.path.exists(json_path):
            return f"No extracted hyperparameter file found for paper '{target_paper_id}'."
            
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            params = data.get("extracted_parameters", {})
            if not params:
                return f"No parameters extracted for paper '{target_paper_id}'."
                
            formatted = []
            for k, v in params.items():
                if isinstance(v, dict):
                    formatted.append(f"- {k}: {v.get('value')} (Status: {v.get('status', 'EXTRACTED')}, Conf: {v.get('confidence', 0)}%)")
                else:
                    formatted.append(f"- {k}: {v}")
            return f"Approved Parameters for '{target_paper_id}':\n" + "\n".join(formatted)
        except Exception as e:
            return f"Error loading parameters for paper '{target_paper_id}': {str(e)}"
