import os
import json
from app.tools.base_tool import BaseTool
from app.retrieval.knowledge_graph import PaperKnowledgeGraph
from app.core.config import settings


class KnowledgeGraphTool(BaseTool):
    name = "query_knowledge_graph"
    description = (
        "Queries the 7-level NetworkX Knowledge Graph for architectural module dependencies, "
        "evidence tracing (trace <param>), consistency validation (validate), "
        "tensor topology (topology), or component relationship paths."
    )

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

        q_clean = (query or "").strip().lower()

        # 1. Architecture Topology / CodeGen Order
        if not q_clean or q_clean in ["all", "topology", "architecture", "overview", "dag", "mermaid", "flowchart"]:
            topology = kg.get_codegen_topology()
            topology_lines = [
                f"{idx}. {t['label']} [{t['type']}] (in={t['in_dim']}, out={t['out_dim']})"
                for idx, t in enumerate(topology, start=1)
            ]
            mermaid_flow = kg.generate_mermaid_flowchart()
            return f"Paper Architectural Execution DAG:\n" + "\n".join(topology_lines) + f"\n\nDynamic Mermaid Architecture Diagram:\n{mermaid_flow}"

        # 2. Consistency Validation
        if q_clean in ["validate", "consistency", "check", "audit"]:
            audit = kg.validate_consistency()
            return (
                f"Knowledge Graph Consistency Audit: {audit['status']}\n"
                f"- Directed Acyclic Graph: {audit['is_directed_acyclic_graph']}\n"
                f"- Total Components: {audit['total_components']}\n"
                f"- Orphan Components: {len(audit['orphan_components'])}\n"
                f"- Unattached Parameters: {len(audit['unattached_parameters'])}\n"
                f"- Verdict: {audit['verdict']}"
            )

        # 3. Evidence Tracing (trace <param_or_component>)
        if q_clean.startswith("trace"):
            target = q_clean.replace("trace", "").strip()
            trace_res = kg.trace_parameter_evidence(target)
            if not trace_res.get("found"):
                return f"Evidence Tracing: {trace_res.get('error')}"
            path_str = " -> ".join(trace_res["provenance_path"])
            return (
                f"Evidence Tracing for '{target}':\n"
                f"- Provenance Chain: {path_str}\n"
                f"- Grounding Section: {trace_res.get('grounding_section')}\n"
                f"- Section Quote: {trace_res.get('evidence_quote')}"
            )

        # 4. Shortest Path Query (e.g. "path encoder to classifier")
        if " to " in q_clean:
            parts = q_clean.split(" to ")
            src, dst = parts[0].replace("path", "").strip(), parts[1].strip()
            path = kg.find_dependency_path(src, dst)
            if path:
                return f"Dependency Chain from '{src}' to '{dst}':\n" + " -> ".join(path)
            return f"No directional dependency path found connecting '{src}' to '{dst}'."

        # 5. Node Connection Summary
        return kg.get_node_connections_summary(query)
