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
    vec_tool = VectorSearchTool()
    scholar_tool = ScholarSearchTool()
    arxiv_tool = ArxivSearchTool()
    param_tool = HyperparameterTool()
    mem_tool = EpisodicMemoryTool()
    canon_tool = CanonicalDocumentTool()
    graph_tool = KnowledgeGraphTool()

    registry = {
        # Canonical names
        vec_tool.name: vec_tool,
        scholar_tool.name: scholar_tool,
        arxiv_tool.name: arxiv_tool,
        param_tool.name: param_tool,
        mem_tool.name: mem_tool,
        canon_tool.name: canon_tool,
        graph_tool.name: graph_tool,

        # Aliases for ReAct flexibility
        "search_paper_chunks": vec_tool,
        "search_paper": vec_tool,
        "search_chunks": vec_tool,
        "paper_search": vec_tool,
        "vector_search": vec_tool,

        "get_canonical_document": canon_tool,
        "canonical_document": canon_tool,
        "canonical_doc": canon_tool,
        "get_sections": canon_tool,
        "get_tables": canon_tool,
        "get_equations": canon_tool,
        "get_abstract": canon_tool,

        "get_hyperparameters": param_tool,
        "hyperparameters": param_tool,
        "get_params": param_tool,
        "approved_parameters": param_tool,

        "query_knowledge_graph": graph_tool,
        "knowledge_graph": graph_tool,
        "graph_search": graph_tool,

        "search_scholar": scholar_tool,
        "scholar_search": scholar_tool,

        "search_arxiv": arxiv_tool,
        "arxiv_search": arxiv_tool,

        "query_episodic_memory": mem_tool,
        "episodic_memory": mem_tool,
    }
    return registry
