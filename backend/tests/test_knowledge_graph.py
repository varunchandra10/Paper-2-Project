"""
Phase 15: Tests for 7-Level Knowledge Graph & Architectural Capabilities.

Verifies:
1. 7-Level hierarchy generation (Paper -> Section -> Concept -> Component -> Parameter -> Dependency -> Implementation).
2. Dependency reasoning and topological execution ordering.
3. Evidence tracing from Parameter back to Section and Paper.
4. Architecture visualization export (React Flow / D3 schema).
5. Graph consistency auditing and orphan detection.
6. Component relationship queries and shortest paths.
7. Agent tool and FastAPI endpoints.
"""

import os
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.retrieval.knowledge_graph import PaperKnowledgeGraph, TIER_METADATA
from app.tools.graph_search_tool import KnowledgeGraphTool
from main import app

client = TestClient(app)

SAMPLE_CANONICAL_DOC = {
    "paper_id": "test_kg_paper",
    "title": "Cross-Attention Transformers for Remote Sensing",
    "metadata": {
        "title": "Cross-Attention Transformers for Remote Sensing",
        "authors": ["Dr. Researcher", "Prof. Scientist"],
        "domain": "Deep Learning / Remote Sensing"
    },
    "sections": [
        ("1. Introduction", "Multimodal alignment is challenging in satellite imagery."),
        ("2. Related Work", "Prior CNN architectures lacked global spatial-spectral context."),
        ("3. Proposed Methodology", "We propose a dual-branch encoder with a cross-attention fusion bottleneck."),
        ("4. Experiments", "Evaluating accuracy with learning rate 0.0001 and batch size 16."),
        ("5. Conclusion", "The cross-attention model establishes new state of the art.")
    ],
    "modules": [
        {"name": "test_kg_paper_InputProjection", "type": "InputLayer", "in_dim": "raw_input", "out_dim": "d_model"},
        {"name": "test_kg_paper_FeatureExtractor", "type": "EncoderBackbone", "in_dim": "d_model", "out_dim": "d_model"},
        {"name": "test_kg_paper_AttentionFusion", "type": "CrossAttentionBlock", "in_dim": "d_model", "out_dim": "d_model"},
        {"name": "test_kg_paper_OutputHead", "type": "ClassifierHead", "in_dim": "d_model", "out_dim": "num_classes"}
    ],
    "hyperparameters": {
        "d_model": 64,
        "num_heads": 4,
        "learning_rate": 0.0001,
        "batch_size": 16
    }
}


@pytest.fixture
def sample_kg(tmp_path, monkeypatch):
    """Initializes PaperKnowledgeGraph in isolated temporary storage."""
    graph_dir = tmp_path / "knowledge_graphs"
    graph_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.retrieval.knowledge_graph.GRAPHS_DIR", str(graph_dir))

    kg = PaperKnowledgeGraph()
    kg.storage_dir = str(graph_dir)
    kg.build_from_canonical(SAMPLE_CANONICAL_DOC, paper_id="paper_test_kg")
    return kg


def test_7_level_hierarchy_generation(sample_kg):
    """Verifies all 7 tiers are represented with proper attributes and edge types."""
    g = sample_kg.graph
    assert len(g.nodes) > 10
    assert len(g.edges) > 10

    # Collect tiers present
    tiers_present = set(d.get("tier") for n, d in g.nodes(data=True) if "tier" in d)
    # Tiers 1 to 5 and 7 are node tiers
    assert 1 in tiers_present  # Paper
    assert 2 in tiers_present  # Section
    assert 3 in tiers_present  # Concept
    assert 4 in tiers_present  # Component
    assert 5 in tiers_present  # Parameter
    assert 7 in tiers_present  # Implementation

    # Tier 6 (Dependency) is edge relation
    feed_edges = [(u, v) for u, v, d in g.edges(data=True) if d.get("relation") == "feeds_into"]
    assert len(feed_edges) >= 3


def test_dependency_reasoning_and_topology(sample_kg):
    """Verifies topological sorting and tensor flow dimensions."""
    topology = sample_kg.get_codegen_topology()
    assert len(topology) == 4

    # Execution order check
    labels = [t["label"] for t in topology]
    assert "InputProjection" in labels[0]
    assert "FeatureExtractor" in labels[1]
    assert "AttentionFusion" in labels[2]
    assert "OutputHead" in labels[3]

    # Verify input/output dimension continuity
    for idx in range(len(topology) - 1):
        curr_out = topology[idx]["out_dim"]
        next_in = topology[idx + 1]["in_dim"]
        assert curr_out == next_in


def test_evidence_tracing(sample_kg):
    """Verifies backward provenance tracing from Parameter to Section and Paper."""
    trace_res = sample_kg.trace_parameter_evidence("d_model")
    assert trace_res["found"] is True
    assert "d_model" in trace_res["target"]

    # Provenance path must contain Section and Paper
    path = trace_res["provenance_path"]
    assert any("paper_" in node for node in path)
    assert any("Section:" in node for node in path)
    assert len(trace_res["evidence_quote"]) > 5


def test_architecture_visualization_export(sample_kg):
    """Verifies visualization schema compatibility with React Flow and D3."""
    viz = sample_kg.export_visualization_graph()
    assert viz["paper_id"] == sample_kg.paper_id
    assert len(viz["nodes"]) == len(sample_kg.graph.nodes)
    assert len(viz["edges"]) == len(sample_kg.graph.edges)

    # Check color badges and tier legend
    for n in viz["nodes"]:
        assert "tier" in n
        assert "color" in n
        assert "badge" in n
    assert 1 in viz["tier_legend"]
    assert 7 in viz["tier_legend"]


def test_consistency_validation_and_orphan_detection(sample_kg):
    """Verifies consistency audit, DAG acyclicity, and orphan detection."""
    audit = sample_kg.validate_consistency()
    assert audit["is_directed_acyclic_graph"] is True
    assert audit["verdict"] == "PASSED"
    assert len(audit["orphan_components"]) == 0

    # Inject an orphan component and verify audit catches it
    sample_kg.graph.add_node("Component:OrphanModule", node_type="component", tier=4)
    audit_orphan = sample_kg.validate_consistency()
    assert "Component:OrphanModule" in audit_orphan["orphan_components"]
    assert audit_orphan["verdict"] == "WARNINGS_DETECTED"


def test_component_relationship_queries(sample_kg):
    """Verifies shortest path finding and node connections summary."""
    # Shortest path between InputProjection and OutputHead
    path = sample_kg.find_dependency_path("InputProjection", "OutputHead")
    assert len(path) >= 2
    assert "InputProjection" in path[0]
    assert "OutputHead" in path[-1]

    # Node connection summary
    summary = sample_kg.get_node_connections_summary("AttentionFusion")
    assert "Knowledge Graph Node" in summary
    assert "feeds_into" in summary or "realizes_concept" in summary


def test_agent_graph_search_tool(sample_kg, monkeypatch):
    """Verifies KnowledgeGraphTool execution with topology, validate, trace, and path commands."""
    tool = KnowledgeGraphTool()
    monkeypatch.setattr("app.tools.graph_search_tool.PaperKnowledgeGraph", lambda pid: sample_kg)

    # 1. Topology
    top_str = tool.execute(query="topology", paper_id=sample_kg.paper_id)
    assert "Execution DAG" in top_str
    assert "AttentionFusion" in top_str

    # 2. Validation
    val_str = tool.execute(query="validate", paper_id=sample_kg.paper_id)
    assert "Consistency Audit" in val_str
    assert "Directed Acyclic Graph: True" in val_str

    # 3. Evidence Tracing
    trace_str = tool.execute(query="trace d_model", paper_id=sample_kg.paper_id)
    assert "Evidence Tracing" in trace_str
    assert "Provenance Chain" in trace_str

    # 4. Path Query
    path_str = tool.execute(query="path InputProjection to OutputHead", paper_id=sample_kg.paper_id)
    assert "Dependency Chain" in path_str


def test_fastapi_knowledge_graph_endpoints(sample_kg, monkeypatch):
    """Verifies FastAPI endpoints for graph visualization, consistency audit, and evidence trace."""
    monkeypatch.setattr("app.api.v1.endpoints.papers.PaperKnowledgeGraph", lambda pid: sample_kg)

    # 1. GET /papers/{paper_id}/knowledge_graph
    resp = client.get(f"/api/v1/papers/{sample_kg.paper_id}/knowledge_graph")
    assert resp.status_code == 200
    data = resp.json()
    assert data["hierarchy_levels"] == 7
    assert "visualization" in data
    assert "consistency" in data

    # 2. GET /papers/{paper_id}/knowledge_graph/validate
    resp_val = client.get(f"/api/v1/papers/{sample_kg.paper_id}/knowledge_graph/validate")
    assert resp_val.status_code == 200
    assert resp_val.json()["is_directed_acyclic_graph"] is True

    # 3. GET /papers/{paper_id}/knowledge_graph/trace/{entity_name}
    resp_tr = client.get(f"/api/v1/papers/{sample_kg.paper_id}/knowledge_graph/trace/d_model")
    assert resp_tr.status_code == 200
    assert resp_tr.json()["found"] is True
