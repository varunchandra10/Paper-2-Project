import os
import json
from app.tools.base_tool import BaseTool
from app.core.config import settings


class HyperparameterTool(BaseTool):
    name = "get_hyperparameters"
    description = "Retrieves extracted and user-approved hyperparameters for a given paper."

    def execute(self, paper_id: str) -> str:
        if not paper_id:
            return "No paper ID specified."
            
        json_path = os.path.join(settings.EXTRACTED_JSON_DIR, f"{paper_id}.json")
        if not os.path.exists(json_path):
            return f"No extracted hyperparameter file found for paper '{paper_id}'."
            
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            params = data.get("extracted_parameters", {})
            if not params:
                return f"No parameters extracted for paper '{paper_id}'."
                
            formatted = []
            for k, v in params.items():
                if isinstance(v, dict):
                    formatted.append(f"- {k}: {v.get('value')} (Status: {v.get('status', 'EXTRACTED')}, Conf: {v.get('confidence', 0)}%)")
            return f"Approved Parameters for '{paper_id}':\n" + "\n".join(formatted)
        except Exception as e:
            return f"Error loading parameters for paper '{paper_id}': {str(e)}"
