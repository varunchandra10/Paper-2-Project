import os
import json
import networkx as nx
from typing import Dict, Any, List, Optional
from app.core.config import settings

GRAPHS_DIR = getattr(settings, "KNOWLEDGE_GRAPHS_DIR", os.path.join(settings.STORAGE_DIR, "knowledge_graphs"))
os.makedirs(GRAPHS_DIR, exist_ok=True)


class PaperKnowledgeGraph:
    """In-Memory Knowledge Graph using NetworkX to map architectural modules,

    hyperparameters, loss functions, and tensor dependencies per paper.
    """

    def __init__(self, paper_id: Optional[str] = None):
        self.paper_id = paper_id
        self.graph = nx.DiGraph()
        self.storage_dir = GRAPHS_DIR
        if paper_id:
            self.load_or_create(paper_id)

    def load_or_create(self, paper_id: str):
        """Loads graph from JSON cache if available, or creates a new graph."""
        self.paper_id = paper_id
        file_path = os.path.join(self.storage_dir, f"{paper_id}_graph.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.graph = nx.node_link_graph(data)
                return
            except Exception as e:
                print(f"[GRAPH WARN] Failed loading cached graph ({e}), initializing fresh graph.")
        self.graph = nx.DiGraph()

    def save(self):
        """Persists graph structure to paper-specific JSON file."""
        if not self.paper_id:
            return
        file_path = os.path.join(self.storage_dir, f"{self.paper_id}_graph.json")
        try:
            data = nx.node_link_data(self.graph)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[GRAPH WARN] Failed to save graph to {file_path}: {e}")

    def build_from_canonical(self, canonical_data: Dict[str, Any]):
        """Builds directed graph nodes and edges dynamically from canonical paper sections and extractions."""
        self.graph.clear()
        
        # Root Paper Node
        paper_id = canonical_data.get("paper_id", self.paper_id or "unknown_paper")
        self.paper_id = paper_id
        paper_title = canonical_data.get("title") or canonical_data.get("parsed_title") or paper_id
        self.graph.add_node(paper_id, node_type="paper", title=paper_title)

        # 1. Dynamic Section Hierarchy & Sequential Flow Nodes
        sections = canonical_data.get("sections", [])
        sec_items = []
        if isinstance(sections, dict):
            sec_items = list(sections.items())
        elif isinstance(sections, list):
            for item in sections:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    sec_items.append((item[0], item[1]))
                elif isinstance(item, dict):
                    sec_items.append((item.get("title", "Section"), item.get("content", "")))
                elif isinstance(item, str):
                    sec_items.append((item, ""))

        prev_sec_node = None
        all_text_concat = ""

        for idx, (s_title, s_content) in enumerate(sec_items, start=1):
            clean_sec_title = str(s_title).strip()
            if not clean_sec_title:
                continue
            sec_node = f"Section:{clean_sec_title}"
            all_text_concat += " " + str(s_content)
            
            self.graph.add_node(sec_node, node_type="section", section_title=clean_sec_title, index=idx)
            self.graph.add_edge(paper_id, sec_node, relation="has_section")
            if prev_sec_node:
                self.graph.add_edge(prev_sec_node, sec_node, relation="followed_by")
            prev_sec_node = sec_node

        # 2. Architectural Modules / Layers (Extracted or Inferred from Sections)
        modules = canonical_data.get("modules", [])
        if not modules:
            # Build dynamic modules from paper section titles or content
            modules = []
            sec_names_upper = [s[0].upper() for s in sec_items if isinstance(s, (list, tuple))]
            
            if any("ENCODER" in s or "METHOD" in s or "PROPOSED" in s or "APPROACH" in s for s in sec_names_upper):
                modules.append({"name": f"{paper_id}_FeatureExtractor", "type": "EncoderModule", "out_dim": "FeatureMap"})
                modules.append({"name": f"{paper_id}_AttentionFusion", "type": "FusionModule", "out_dim": "FusedEmbeddings"})
                modules.append({"name": f"{paper_id}_ClassifierHead", "type": "OutputHead", "out_dim": "Predictions"})
            else:
                modules.append({"name": f"{paper_id}_InputRepresentation", "type": "EmbeddingLayer", "out_dim": "d_model"})
                modules.append({"name": f"{paper_id}_CoreProcessingBlock", "type": "BackboneBlock", "out_dim": "d_model"})
                modules.append({"name": f"{paper_id}_OutputTaskHead", "type": "LinearHead", "out_dim": "num_classes"})

        prev_mod = None
        for mod in modules:
            mod_name = mod.get("name", "Module")
            self.graph.add_node(mod_name, node_type="module", **mod)
            self.graph.add_edge(paper_id, mod_name, relation="contains_module")
            if prev_mod:
                self.graph.add_edge(prev_mod, mod_name, relation="feeds_into")
            prev_mod = mod_name

        # 3. Dynamic Technical Concepts & Frameworks Detection
        text_lower = (paper_title + " " + all_text_concat).lower()
        tech_concepts = []
        for kw in ["pytorch", "tensorflow", "transformer", "attention", "cnn", "resnet", "swin", "unet", "adamw", "focal loss"]:
            if kw in text_lower:
                tech_concepts.append(kw.title())

        for concept in tech_concepts:
            c_node = f"Concept:{concept}"
            self.graph.add_node(c_node, node_type="concept", name=concept)
            self.graph.add_edge(paper_id, c_node, relation="uses_technology")

        # 4. Hyperparameters & Hardware
        params = canonical_data.get("hyperparameters", {"learning_rate": 0.0001, "batch_size": 16})
        if isinstance(params, dict):
            for k, v in params.items():
                param_node = f"Param:{k}"
                self.graph.add_node(param_node, node_type="hyperparameter", key=k, value=v)
                self.graph.add_edge(paper_id, param_node, relation="uses_parameter")

        self.save()
        return self.graph

    def get_codegen_topology(self) -> List[Dict[str, Any]]:
        """Returns ordered list of modules and their parameter bindings for PyTorch CodeGen."""
        topology = []
        module_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "module"]
        
        for n in module_nodes:
            data = self.graph.nodes[n]
            # Find incoming feeds_into edges
            incoming = [u for u, v, d in self.graph.in_edges(n, data=True) if d.get("relation") == "feeds_into"]
            outgoing = [v for u, v, d in self.graph.out_edges(n, data=True) if d.get("relation") == "feeds_into"]
            
            topology.append({
                "module": n,
                "type": data.get("type", "layer"),
                "inputs_from": incoming,
                "outputs_to": outgoing,
                "out_dim": data.get("out_dim", "d_model")
            })
        return topology

    def get_node_connections_summary(self, target_name: str) -> str:
        """Traces and formats relationships for a specific module or concept."""
        matches = [n for n in self.graph.nodes() if target_name.lower() in n.lower()]
        if not matches:
            return f"No Knowledge Graph nodes matched '{target_name}'."
            
        node = matches[0]
        in_edges = [(u, d.get("relation", "connected")) for u, v, d in self.graph.in_edges(node, data=True)]
        out_edges = [(v, d.get("relation", "connected")) for u, v, d in self.graph.out_edges(node, data=True)]
        
        lines = [f"**Knowledge Graph Node:** `{node}`"]
        if in_edges:
            lines.append("  *Incoming Connections:*")
            for u, rel in in_edges:
                lines.append(f"    - [{u}] --({rel})--> [{node}]")
        if out_edges:
            lines.append("  *Outgoing Connections:*")
            for v, rel in out_edges:
                lines.append(f"    - [{node}] --({rel})--> [{v}]")
                
        return "\n".join(lines)
