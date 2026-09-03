from typing import List, Dict
from app.tools.base_tool import BaseTool
from app.tools.vector_search_tool import VectorSearchTool
from app.tools.scholar_search_tool import ScholarSearchTool
from app.tools.arxiv_search_tool import ArxivSearchTool
from app.tools.hyperparameter_tool import HyperparameterTool
from app.tools.episodic_memory_tool import EpisodicMemoryTool
from app.tools.canonical_document_tool import CanonicalDocumentTool
from app.tools.graph_search_tool import KnowledgeGraphTool


def get_all_tools() -> Dict[str, BaseTool]:
    """Returns registry dictionary mapping tool names to tool instances."""
    tools = [
        VectorSearchTool(),
        ScholarSearchTool(),
        ArxivSearchTool(),
        HyperparameterTool(),
        EpisodicMemoryTool(),
        CanonicalDocumentTool(),
        KnowledgeGraphTool()
    ]
    registry = {t.name: t for t in tools}
    registry["search_paper_chunks"] = registry["vector_search"]
    registry["search_arxiv"] = registry["search_arxiv_papers"]
    registry["graph_search"] = registry["query_knowledge_graph"]
    return registry
