import os
from app.tools.base_tool import BaseTool
from app.retrieval.knowledge_graph import PaperKnowledgeGraph
from app.core.config import settings


class KnowledgeGraphTool(BaseTool):
    name = "query_knowledge_graph"
    description = "Queries the NetworkX Knowledge Graph for architectural module dependencies, tensor paths, and hyperparameter bindings."

    def execute(self, query: str = "", paper_id: str = None, *args, **kwargs) -> str:
        target_paper_id = paper_id or kwargs.get("paper_id")
        if not target_paper_id and os.path.exists(settings.EXTRACTED_JSON_DIR):
            files = [f for f in os.listdir(settings.EXTRACTED_JSON_DIR) if f.endswith(".json")]
            if len(files) == 1:
                target_paper_id = files[0].replace(".json", "")

        if not target_paper_id:
            return "No active paper context specified for Knowledge Graph query."
            
        kg = PaperKnowledgeGraph(target_paper_id)
        if len(kg.graph.nodes) == 0:
            return f"Knowledge Graph for paper '{target_paper_id}' is empty or uninitialized."
            
        if not query or query.strip() in ["all", "topology", "architecture", "overview"]:
            topology = kg.get_codegen_topology()
            topology_str = ", ".join([f"{t['module']} ({t['type']})" for t in topology])
            return f"Paper Architectural Topology: {topology_str}"
            
        return kg.get_node_connections_summary(query)
