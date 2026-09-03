from app.tools.base_tool import BaseTool
from app.retrieval.knowledge_graph import PaperKnowledgeGraph


class KnowledgeGraphTool(BaseTool):
    name = "query_knowledge_graph"
    description = "Queries the NetworkX Knowledge Graph for architectural module dependencies, tensor paths, and hyperparameter bindings."

    def execute(self, query: str, paper_id: str = None) -> str:
        if not paper_id:
            return "No active paper context specified for Knowledge Graph query."
            
        kg = PaperKnowledgeGraph(paper_id)
        if len(kg.graph.nodes) == 0:
            return f"Knowledge Graph for paper '{paper_id}' is empty or uninitialized."
            
        if not query:
            topology = kg.get_codegen_topology()
            topology_str = ", ".join([f"{t['module']} ({t['type']})" for t in topology])
            return f"Paper Architectural Topology: {topology_str}"
            
        return kg.get_node_connections_summary(query)
