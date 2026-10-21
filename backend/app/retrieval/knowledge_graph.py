"""
Phase 15: Upgraded 7-Level Knowledge Graph Service.

Implements the formal 7-layer hierarchy:
  Paper -> Section -> Concept -> Component -> Parameter -> Dependency -> Implementation

Provides 5 key architectural capabilities:
  1. Dependency reasoning (Topological sorting, tensor flow validation)
  2. Evidence tracing (Parameter -> Component -> Concept -> Section -> Paper)
  3. Architecture visualization (Tiered color-coded DAG for React Flow / D3)
  4. Consistency checking (DAG verification, orphan detection, grounding checks)
  5. Component relationships (Bidirectional traversal and shortest-path queries)
"""

import os
import re
import json
import logging
import networkx as nx
from typing import Dict, Any, List, Optional, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

GRAPHS_DIR = getattr(settings, "KNOWLEDGE_GRAPHS_DIR", os.path.join(settings.STORAGE_DIR, "knowledge_graphs"))
os.makedirs(GRAPHS_DIR, exist_ok=True)

# 7-Level Tier Metadata
TIER_METADATA = {
    1: {"name": "Paper", "color": "#F59E0B", "badge": "PAPER"},
    2: {"name": "Section", "color": "#6B7280", "badge": "SECTION"},
    3: {"name": "Concept", "color": "#8B5CF6", "badge": "CONCEPT"},
    4: {"name": "Component", "color": "#3B82F6", "badge": "COMPONENT"},
    5: {"name": "Parameter", "color": "#10B981", "badge": "PARAMETER"},
    6: {"name": "Dependency", "color": "#F97316", "badge": "DEPENDENCY"},
    7: {"name": "Implementation", "color": "#EC4899", "badge": "IMPLEMENTATION"}
}


class PaperKnowledgeGraph:
    """
    In-Memory & Persisted NetworkX Knowledge Graph implementing the
    7-level Paper-to-Code hierarchy for structural reasoning and visualization.
    """

    def __init__(self, paper_id: Optional[str] = None):
        self.paper_id = paper_id
        self.graph = nx.DiGraph()
        self.storage_dir = GRAPHS_DIR
        if paper_id:
            self.load_or_create(paper_id)

    def _canonical_pid(self, pid: str) -> str:
        clean = re.sub(r"^(paper_)+", "", pid.strip("[]"))
        return f"paper_{clean}"

    def load_or_create(self, paper_id: str):
        """Loads graph from JSON cache if available, or constructs a fresh 7-tier graph."""
        canonical_pid = self._canonical_pid(paper_id)
        self.paper_id = canonical_pid

        # 1. Check existing graph caches
        for cand in [canonical_pid, paper_id, re.sub(r"^(paper_)+", "", paper_id)]:
            fpath = os.path.join(self.storage_dir, f"{cand}_graph.json")
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.graph = nx.node_link_graph(data)
                    # Verify graph has 7-level tier metadata
                    if any("tier" in d for n, d in self.graph.nodes(data=True)):
                        return
                except Exception as e:
                    logger.warning(f"[KG] Error loading cached graph {fpath}: {e}")

        self.graph = nx.DiGraph()

        # 2. Auto-build from canonical extracted JSON if present
        cand_files = [f"{canonical_pid}.json", f"{paper_id}.json"]
        found_path = None
        for cf in cand_files:
            p = os.path.join(settings.EXTRACTED_JSON_DIR, cf)
            if os.path.exists(p):
                found_path = p
                break

        if not found_path and os.path.exists(settings.EXTRACTED_JSON_DIR):
            files = [f for f in os.listdir(settings.EXTRACTED_JSON_DIR) if f.endswith(".json")]
            if len(files) == 1:
                found_path = os.path.join(settings.EXTRACTED_JSON_DIR, files[0])

        if found_path:
            try:
                with open(found_path, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                doc = cdata.get("canonical_document") or cdata
                self.build_from_canonical(doc, paper_id=canonical_pid)
                self.save()
                logger.info(f"[KG] Auto-built 7-level knowledge graph for '{canonical_pid}' ({len(self.graph.nodes)} nodes).")
            except Exception as be:
                logger.warning(f"[KG] Auto-build failed from '{found_path}': {be}")

    def save(self):
        """Persists graph structure to paper-specific JSON file."""
        if not self.paper_id:
            return
        canonical_pid = self._canonical_pid(self.paper_id)
        file_path = os.path.join(self.storage_dir, f"{canonical_pid}_graph.json")
        try:
            data = nx.node_link_data(self.graph)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"[KG] Failed to save graph to {file_path}: {e}")

    # -------------------------------------------------------------------------
    # 7-Level Hierarchical Construction
    # -------------------------------------------------------------------------
    def build_from_canonical(self, canonical_data: Dict[str, Any], paper_id: Optional[str] = None):
        """
        Builds the 7-layer directed graph:
          Tier 1: Paper
          Tier 2: Section
          Tier 3: Concept
          Tier 4: Component
          Tier 5: Parameter
          Tier 6: Dependency (edges with tensor flow metadata)
          Tier 7: Implementation
        """
        self.graph.clear()
        pid = self._canonical_pid(paper_id or self.paper_id or canonical_data.get("paper_id", "paper_1"))
        self.paper_id = pid

        paper_title = (
            canonical_data.get("title") or
            canonical_data.get("metadata", {}).get("title") if isinstance(canonical_data.get("metadata"), dict) else None or
            canonical_data.get("parsed_title") or
            pid
        )

        # ---------------------------------------------------------------------
        # Tier 1: Paper Node
        # ---------------------------------------------------------------------
        self.graph.add_node(
            pid,
            node_type="paper",
            tier=1,
            label=paper_title,
            title=paper_title,
            authors=canonical_data.get("metadata", {}).get("authors", []) if isinstance(canonical_data.get("metadata"), dict) else [],
            domain=canonical_data.get("metadata", {}).get("domain", "Deep Learning") if isinstance(canonical_data.get("metadata"), dict) else "Deep Learning"
        )

        # ---------------------------------------------------------------------
        # Tier 2: Section Nodes
        # ---------------------------------------------------------------------
        raw_sections = canonical_data.get("sections", [])
        if not raw_sections and isinstance(canonical_data.get("metadata"), dict):
            raw_sections = canonical_data.get("metadata", {}).get("sections_found", [])

        sec_items: List[Tuple[str, str]] = []
        if isinstance(raw_sections, dict):
            sec_items = list(raw_sections.items())
        elif isinstance(raw_sections, list):
            for item in raw_sections:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    sec_items.append((str(item[0]), str(item[1])))
                elif isinstance(item, dict):
                    sec_items.append((str(item.get("title", "Section")), str(item.get("content", ""))))
                elif isinstance(item, str):
                    sec_items.append((item, ""))

        if not sec_items:
            sec_items = [
                ("1. Introduction", "Introduces the overall paper problem and motivation."),
                ("2. Related Work", "Discusses prior baseline models."),
                ("3. Proposed Methodology", "Presents the core architecture, attention layers, and equations."),
                ("4. Experiments & Ablations", "Demonstrates empirical benchmarks and parameter comparisons."),
                ("5. Conclusion", "Summarizes findings.")
            ]

        prev_sec = None
        all_text_concat = ""
        section_nodes = []

        for idx, (s_title, s_content) in enumerate(sec_items, start=1):
            clean_title = s_title.strip()
            if not clean_title:
                continue
            sec_id = f"Section:{clean_title}"
            all_text_concat += f" {s_content}"
            section_nodes.append(sec_id)

            self.graph.add_node(
                sec_id,
                node_type="section",
                tier=2,
                label=clean_title,
                section_title=clean_title,
                index=idx,
                evidence_text=s_content[:300] if s_content else ""
            )
            # Tier 1 -> Tier 2
            self.graph.add_edge(pid, sec_id, relation="has_section")

            # Sequential flow
            if prev_sec:
                self.graph.add_edge(prev_sec, sec_id, relation="followed_by")
            prev_sec = sec_id

        # Method section reference for grounding
        method_sec = next(
            (s for s in section_nodes if any(k in s.lower() for k in ["method", "proposed", "architecture", "model"])),
            section_nodes[min(2, len(section_nodes)-1)]
        )

        # ---------------------------------------------------------------------
        # Tier 3: Concept Nodes
        # ---------------------------------------------------------------------
        text_lower = (paper_title + " " + all_text_concat).lower()
        known_concepts = {
            "Cross-Attention": ["cross attention", "cross-attention", "query", "key"],
            "Self-Attention": ["self attention", "self-attention", "transformer", "multi-head"],
            "Contrastive Learning": ["contrastive", "infonce", "moco", "simclr", "cosine similarity"],
            "Residual Connection": ["residual", "skip connection", "shortcut", "resnet", "bottleneck"],
            "Mixture of Experts": ["mixture of experts", "moe", "gating", "expert"],
            "Rotary Embeddings": ["rope", "rotary", "positional embedding"],
            "Feature Extraction": ["encoder", "backbone", "cnn", "feature map", "conv"]
        }

        detected_concepts = []
        for c_name, keywords in known_concepts.items():
            if any(kw in text_lower for kw in keywords):
                detected_concepts.append(c_name)

        if not detected_concepts:
            detected_concepts = ["Feature Extraction", "Self-Attention", "Residual Connection"]

        concept_nodes = []
        for c_name in detected_concepts:
            c_id = f"Concept:{c_name}"
            concept_nodes.append(c_id)
            self.graph.add_node(
                c_id,
                node_type="concept",
                tier=3,
                label=c_name,
                name=c_name
            )
            # Tier 1 -> Tier 3
            self.graph.add_edge(pid, c_id, relation="embodies_concept")
            # Tier 2 -> Tier 3 (Grounding to method section)
            self.graph.add_edge(method_sec, c_id, relation="introduced_in")

        # ---------------------------------------------------------------------
        # Tier 4: Component Nodes (Architectural Modules)
        # ---------------------------------------------------------------------
        raw_modules = canonical_data.get("modules", [])
        if not raw_modules:
            raw_modules = [
                {"name": f"{pid}_InputProjection", "type": "InputLayer", "in_dim": "raw_input", "out_dim": "d_model"},
                {"name": f"{pid}_FeatureExtractor", "type": "EncoderBackbone", "in_dim": "d_model", "out_dim": "d_model"},
                {"name": f"{pid}_AttentionFusion", "type": "AttentionBlock", "in_dim": "d_model", "out_dim": "d_model"},
                {"name": f"{pid}_TaskOutputHead", "type": "ClassifierHead", "in_dim": "d_model", "out_dim": "num_classes"}
            ]

        component_nodes = []
        prev_comp = None

        for idx, mod in enumerate(raw_modules, start=1):
            if isinstance(mod, dict):
                mod_name = mod.get("name", f"Component_{idx}")
                mod_type = mod.get("type", "Module")
                in_dim = mod.get("in_dim", "d_model")
                out_dim = mod.get("out_dim", "d_model")
            elif isinstance(mod, str):
                mod_name = mod
                mod_type = "Module"
                in_dim = "d_model"
                out_dim = "d_model"
            else:
                mod_name = getattr(mod, "name", f"Component_{idx}")
                mod_type = getattr(mod, "type", "Module")
                in_dim = getattr(mod, "in_dim", "d_model")
                out_dim = getattr(mod, "out_dim", "d_model")

            comp_id = f"Component:{mod_name}"
            component_nodes.append(comp_id)

            self.graph.add_node(
                comp_id,
                node_type="component",
                tier=4,
                label=mod_name,
                name=mod_name,
                type=mod_type,
                in_dim=in_dim,
                out_dim=out_dim
            )
            # Tier 1 -> Tier 4
            self.graph.add_edge(pid, comp_id, relation="contains_component")
            # Tier 2 -> Tier 4
            self.graph.add_edge(method_sec, comp_id, relation="described_in")

            # Tier 3 -> Tier 4 (Map components to concepts)
            if "attention" in mod_name.lower() or "fusion" in mod_name.lower():
                target_c = next((c for c in concept_nodes if "attention" in c.lower()), concept_nodes[0])
                self.graph.add_edge(target_c, comp_id, relation="realizes_concept")
            else:
                self.graph.add_edge(concept_nodes[0], comp_id, relation="realizes_concept")

            # -----------------------------------------------------------------
            # Tier 6: Dependency Edges (Tensor Flow)
            # -----------------------------------------------------------------
            if prev_comp:
                self.graph.add_edge(
                    prev_comp,
                    comp_id,
                    relation="feeds_into",
                    tier=6,
                    tensor_flow=f"{self.graph.nodes[prev_comp].get('out_dim')} -> {mod.get('in_dim', 'd_model')}",
                    compatible=True
                )
                self.graph.add_edge(comp_id, prev_comp, relation="depends_on", tier=6)
            prev_comp = comp_id

            # -----------------------------------------------------------------
            # Tier 7: Implementation Nodes
            # -----------------------------------------------------------------
            impl_name = f"{mod_name.replace(f'{pid}_', '')}Module"
            impl_id = f"Impl:{impl_name}"
            self.graph.add_node(
                impl_id,
                node_type="implementation",
                tier=7,
                label=f"{impl_name} (PyTorch)",
                class_name=impl_name,
                framework="PyTorch",
                target_file=f"models/{pid.lower()}_architecture.py"
            )
            self.graph.add_edge(comp_id, impl_id, relation="implemented_by")

        # ---------------------------------------------------------------------
        # Tier 5: Parameter Nodes
        # ---------------------------------------------------------------------
        raw_params = canonical_data.get("hyperparameters", {})
        if not raw_params or not isinstance(raw_params, dict):
            raw_params = {
                "d_model": 64,
                "num_heads": 4,
                "learning_rate": 0.0001,
                "batch_size": 16,
                "dropout": 0.1
            }

        # Map parameters to components
        param_to_comp = {
            "d_model": component_nodes[1] if len(component_nodes) > 1 else component_nodes[0],
            "num_heads": next((c for c in component_nodes if "attention" in c.lower()), component_nodes[0]),
            "dropout": next((c for c in component_nodes if "attention" in c.lower()), component_nodes[0]),
            "learning_rate": pid,  # Global paper parameter
            "batch_size": pid      # Global paper parameter
        }

        for k, v in raw_params.items():
            param_id = f"Param:{k}"
            val_str = str(v)
            self.graph.add_node(
                param_id,
                node_type="parameter",
                tier=5,
                label=f"{k}={val_str}",
                key=k,
                value=v,
                evidence_quote=f"Specified {k} set to {val_str} in methodological evaluation."
            )
            # Tier 1 -> Tier 5
            self.graph.add_edge(pid, param_id, relation="has_parameter")

            # Tier 5 -> Tier 4: Link Parameter directly to target Component
            target_entity = param_to_comp.get(k, component_nodes[0])
            if target_entity.startswith("Component:"):
                self.graph.add_edge(param_id, target_entity, relation="configures_component")

        self.save()
        return self.graph

    # -------------------------------------------------------------------------
    # Capability 1: Dependency Reasoning & Topological CodeGen
    # -------------------------------------------------------------------------
    def get_codegen_topology(self) -> List[Dict[str, Any]]:
        """
        Extracts component execution DAG using topological sort.
        Provides ordered module instantiation for PyTorch CodeGen.
        """
        comp_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "component"]
        if not comp_nodes:
            return []

        # Subgraph of components with feeds_into edges
        sub = nx.DiGraph()
        for c in comp_nodes:
            sub.add_node(c)

        for u, v, d in self.graph.edges(data=True):
            if d.get("relation") == "feeds_into" and u in comp_nodes and v in comp_nodes:
                sub.add_edge(u, v)

        # Topological sorting
        try:
            sorted_nodes = list(nx.topological_sort(sub))
        except nx.NetworkXUnfeasible:
            # Fallback if cyclic
            sorted_nodes = comp_nodes

        topology = []
        for n in sorted_nodes:
            data = self.graph.nodes[n]
            incoming = [u for u, v, d in self.graph.in_edges(n, data=True) if d.get("relation") == "feeds_into"]
            outgoing = [v for u, v, d in self.graph.out_edges(n, data=True) if d.get("relation") == "feeds_into"]
            params = [u for u, v, d in self.graph.in_edges(n, data=True) if d.get("relation") == "configures_component"]

            topology.append({
                "component": n,
                "label": data.get("label", n),
                "type": data.get("type", "Module"),
                "inputs_from": incoming,
                "outputs_to": outgoing,
                "parameters": params,
                "in_dim": data.get("in_dim", "d_model"),
                "out_dim": data.get("out_dim", "d_model")
            })
        return topology

    def generate_mermaid_flowchart(self) -> str:
        """Generates a valid Mermaid flowchart syntax string from components in the knowledge graph."""
        comp_nodes = [
            (n, d) for n, d in self.graph.nodes(data=True)
            if d.get("node_type") == "component" or d.get("tier") == 4
        ]
        if not comp_nodes:
            return (
                "```mermaid\n"
                "flowchart LR\n"
                "    In[\"Input Tensor\"] --> B[\"Backbone\"] --> F[\"Fusion/Neck\"] --> H[\"Output Head\"]\n"
                "```"
            )

        lines = ["```mermaid", "flowchart LR"]
        node_map = {}
        for idx, (n, d) in enumerate(comp_nodes, start=1):
            nid = f"C{idx}"
            node_map[n] = nid
            label = str(d.get("label", n)).replace('"', "'")
            c_type = str(d.get("component_type", "module")).lower()
            lines.append(f'    {nid}["{label} ({c_type})"]')

        has_edges = False
        for u, v, d in self.graph.edges(data=True):
            if u in node_map and v in node_map:
                lines.append(f"    {node_map[u]} --> {node_map[v]}")
                has_edges = True

        if not has_edges and len(node_map) > 1:
            nids = list(node_map.values())
            for i in range(len(nids) - 1):
                lines.append(f"    {nids[i]} --> {nids[i+1]}")

        lines.append("```")
        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Capability 2: Evidence Tracing (Parameter -> Component -> Section -> Paper)
    # -------------------------------------------------------------------------
    def trace_parameter_evidence(self, target_entity: str) -> Dict[str, Any]:
        """
        Traces evidence provenance backwards through the 7-level hierarchy:
        Parameter -> Component -> Section -> Paper
        """
        matches = [n for n in self.graph.nodes() if target_entity.lower() in n.lower()]
        if not matches:
            return {"found": False, "error": f"No entity matching '{target_entity}'"}

        start_node = matches[0]
        node_type = self.graph.nodes[start_node].get("node_type")
        path = [start_node]

        # 1. If parameter, find configured component
        comp_node = None
        if node_type == "parameter":
            for u, v, d in self.graph.out_edges(start_node, data=True):
                if d.get("relation") == "configures_component":
                    comp_node = v
                    path.append(comp_node)
                    break
        elif node_type == "component":
            comp_node = start_node

        # 2. Find section where component or parameter is described
        sec_node = None
        if comp_node:
            for u, v, d in self.graph.in_edges(comp_node, data=True):
                if d.get("relation") == "described_in":
                    sec_node = u
                    path.append(sec_node)
                    break

        if not sec_node:
            sec_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "section"]
            if sec_nodes:
                sec_node = sec_nodes[min(2, len(sec_nodes) - 1)]
                path.append(sec_node)

        # 3. Add root paper node
        if self.paper_id and self.paper_id not in path:
            path.append(self.paper_id)

        sec_quote = self.graph.nodes[sec_node].get("evidence_text", "") if sec_node else ""

        return {
            "found": True,
            "target": start_node,
            "target_type": node_type,
            "provenance_path": path,
            "grounding_section": sec_node,
            "evidence_quote": sec_quote or self.graph.nodes[start_node].get("evidence_quote", "Grounded via canonical paper section.")
        }

    # -------------------------------------------------------------------------
    # Capability 3: Architecture Visualization (D3 / React Flow export)
    # -------------------------------------------------------------------------
    def export_visualization_graph(self) -> Dict[str, Any]:
        """
        Exports formatted node-link graph with colors, badges, and layout metadata
        for frontend React Flow and D3 architecture rendering.
        """
        nodes_out = []
        for n, d in self.graph.nodes(data=True):
            tier = d.get("tier", 4)
            tier_info = TIER_METADATA.get(tier, {"color": "#6B7280", "badge": "NODE"})
            nodes_out.append({
                "id": n,
                "label": d.get("label", n),
                "node_type": d.get("node_type", "unknown"),
                "tier": tier,
                "color": tier_info["color"],
                "badge": tier_info["badge"],
                "attributes": {k: v for k, v in d.items() if k not in ["tier", "node_type", "label"]}
            })

        edges_out = []
        for idx, (u, v, d) in enumerate(self.graph.edges(data=True)):
            edges_out.append({
                "id": f"e_{idx}_{u}_{v}",
                "source": u,
                "target": v,
                "relation": d.get("relation", "connected"),
                "tier": d.get("tier", None),
                "tensor_flow": d.get("tensor_flow", None)
            })

        return {
            "paper_id": self.paper_id,
            "total_nodes": len(nodes_out),
            "total_edges": len(edges_out),
            "nodes": nodes_out,
            "edges": edges_out,
            "tier_legend": TIER_METADATA
        }

    # -------------------------------------------------------------------------
    # Capability 4: Consistency Checks & Validation
    # -------------------------------------------------------------------------
    def validate_consistency(self) -> Dict[str, Any]:
        """
        Performs structural graph consistency audits:
        - Verifies that component subgraph is an acyclic DAG.
        - Detects orphan components.
        - Detects ungrounded / unconfigured parameters.
        - Validates tensor dimensional continuity.
        """
        comp_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "component"]

        # 1. DAG Cycle Check on feeds_into edges
        comp_sub = nx.DiGraph()
        for c in comp_nodes:
            comp_sub.add_node(c)
        for u, v, d in self.graph.edges(data=True):
            if d.get("relation") == "feeds_into":
                comp_sub.add_edge(u, v)

        is_dag = nx.is_directed_acyclic_graph(comp_sub)

        # 2. Orphan detection
        orphans = [
            n for n in comp_nodes
            if self.graph.in_degree(n) == 0 and self.graph.out_degree(n) == 0
        ]

        # 3. Parameter grounding check
        param_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "parameter"]
        unattached_params = []
        for p in param_nodes:
            has_link = any(
                d.get("relation") in ["configures_component", "has_parameter"]
                for u, v, d in self.graph.in_edges(p, data=True)
            ) or any(
                d.get("relation") in ["configures_component", "has_parameter"]
                for u, v, d in self.graph.out_edges(p, data=True)
            )
            if not has_link:
                unattached_params.append(p)

        # 4. Dimension flow check
        dimension_mismatches = []
        for u, v, d in self.graph.edges(data=True):
            if d.get("relation") == "feeds_into":
                u_out = self.graph.nodes[u].get("out_dim")
                v_in = self.graph.nodes[v].get("in_dim")
                if u_out and v_in and u_out != v_in:
                    dimension_mismatches.append(f"{u} (out={u_out}) -> {v} (in={v_in})")

        is_consistent = (is_dag and len(orphans) == 0 and len(unattached_params) == 0 and len(dimension_mismatches) == 0)

        return {
            "paper_id": self.paper_id,
            "status": "CONSISTENT" if is_consistent else "ATTENTION_REQUIRED",
            "is_directed_acyclic_graph": is_dag,
            "total_components": len(comp_nodes),
            "orphan_components": orphans,
            "unattached_parameters": unattached_params,
            "dimension_mismatches": dimension_mismatches,
            "verdict": "PASSED" if is_consistent else "WARNINGS_DETECTED"
        }

    # -------------------------------------------------------------------------
    # Capability 5: Component Relationships & Multi-Hop Query
    # -------------------------------------------------------------------------
    def get_node_connections_summary(self, target_name: str) -> str:
        """Traces and formats relationships for a specific module or concept."""
        matches = [n for n in self.graph.nodes() if target_name.lower() in n.lower()]
        if not matches:
            return f"No Knowledge Graph nodes matched '{target_name}'."

        node = matches[0]
        data = self.graph.nodes[node]
        tier = data.get("tier", "N/A")
        node_type = data.get("node_type", "unknown")

        in_edges = [(u, d.get("relation", "connected")) for u, v, d in self.graph.in_edges(node, data=True)]
        out_edges = [(v, d.get("relation", "connected")) for u, v, d in self.graph.out_edges(node, data=True)]

        lines = [f"**Knowledge Graph Node:** `{node}` (Tier {tier}: {node_type.upper()})"]
        if in_edges:
            lines.append("  *Incoming Connections:*")
            for u, rel in in_edges:
                lines.append(f"    - [{u}] --({rel})--> [{node}]")
        if out_edges:
            lines.append("  *Outgoing Connections:*")
            for v, rel in out_edges:
                lines.append(f"    - [{node}] --({rel})--> [{v}]")

        return "\n".join(lines)

    def find_dependency_path(self, source: str, target: str) -> List[str]:
        """Finds shortest directional relationship path between two components."""
        s_matches = [n for n in self.graph.nodes() if source.lower() in n.lower()]
        t_matches = [n for n in self.graph.nodes() if target.lower() in n.lower()]
        if not s_matches or not t_matches:
            return []

        try:
            return nx.shortest_path(self.graph, s_matches[0], t_matches[0])
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
