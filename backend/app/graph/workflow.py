from langgraph.graph import StateGraph, START, END
from app.graph.state import PipelineState
from app.graph.nodes.ingestion import ingestion_node
from app.graph.nodes.extraction import parameter_extraction_node
from app.graph.nodes.feasibility import feasibility_node
from app.graph.nodes.sequencing import sequencing_node
from app.graph.nodes.verification import verification_node


def build_pipeline_workflow() -> StateGraph:
    """Builds and compiles the LangGraph StateGraph workflow for paper adaptation."""
    builder = StateGraph(PipelineState)
    
    # 1. Add Nodes
    builder.add_node("ingestion_node", ingestion_node)
    builder.add_node("extraction_node", parameter_extraction_node)
    builder.add_node("feasibility_node", feasibility_node)
    builder.add_node("sequencing_node", sequencing_node)
    builder.add_node("verification_node", verification_node)
    
    # 2. Add Edges
    builder.add_edge(START, "ingestion_node")
    builder.add_edge("ingestion_node", "extraction_node")
    builder.add_edge("extraction_node", "feasibility_node")
    builder.add_edge("feasibility_node", "sequencing_node")
    builder.add_edge("sequencing_node", "verification_node")
    builder.add_edge("verification_node", END)
    
    return builder.compile()


app_workflow = build_pipeline_workflow()
