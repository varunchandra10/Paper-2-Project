"""Deterministic Directed Acyclic Graph (DAG) Validator for Paper-2-Project.
Validates execution sequences, detects cycles with exact traces, identifies
missing/duplicate/orphan dependencies, and produces deterministic topological ordering.
"""

import re
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set, Tuple


class DAGErrorCode(str, Enum):
    EMPTY_PLAN = "EMPTY_PLAN"
    INVALID_NODE_ID = "INVALID_NODE_ID"
    DUPLICATE_NODE = "DUPLICATE_NODE"
    MISSING_DEPENDENCY = "MISSING_DEPENDENCY"
    SELF_DEPENDENCY = "SELF_DEPENDENCY"
    CYCLE_DETECTED = "CYCLE_DETECTED"
    ORPHAN_NODE = "ORPHAN_NODE"


@dataclass
class DAGValidationIssue:
    code: DAGErrorCode
    message: str
    node_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code.value if hasattr(self.code, "value") else str(self.code),
            "message": self.message,
            "node_id": self.node_id,
            "details": self.details or {}
        }


@dataclass
class DAGValidationResult:
    is_valid: bool
    execution_order: List[str] = field(default_factory=list)
    issues: List[DAGValidationIssue] = field(default_factory=list)
    cycle_path: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "execution_order": self.execution_order,
            "issues": [i.to_dict() for i in self.issues],
            "cycle_path": self.cycle_path
        }


class DAGValidator:
    """Independent, deterministic graph validator and topological sorter."""

    NODE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]+$")

    @classmethod
    def validate(cls, steps: List[Any]) -> DAGValidationResult:
        """Validates a list of execution steps (dicts or BuildSequenceStep models).
        Returns DAGValidationResult with boolean validity, execution order, and structured issues.
        """
        issues: List[DAGValidationIssue] = []

        # 1. Check for empty plan
        if not steps:
            issues.append(DAGValidationIssue(
                code=DAGErrorCode.EMPTY_PLAN,
                message="Execution plan contains zero steps."
            ))
            return DAGValidationResult(is_valid=False, issues=issues)

        # 2. Extract step data and validate node IDs
        nodes: List[str] = []
        node_set: Set[str] = set()
        step_dict: Dict[str, Any] = {}
        dep_map: Dict[str, List[str]] = {}

        for idx, s in enumerate(steps):
            name = s.component_name if hasattr(s, "component_name") else s.get("component_name")
            deps = s.dependencies if hasattr(s, "dependencies") else s.get("dependencies", [])

            if not name or not isinstance(name, str) or not name.strip():
                issues.append(DAGValidationIssue(
                    code=DAGErrorCode.INVALID_NODE_ID,
                    message=f"Step index {idx} has an empty or invalid component name.",
                    node_id=str(name)
                ))
                continue

            name = name.strip()
            if not cls.NODE_ID_REGEX.match(name):
                issues.append(DAGValidationIssue(
                    code=DAGErrorCode.INVALID_NODE_ID,
                    message=f"Component name '{name}' contains illegal characters (must be alphanumeric, _, -, .).",
                    node_id=name
                ))
                continue

            if name in node_set:
                issues.append(DAGValidationIssue(
                    code=DAGErrorCode.DUPLICATE_NODE,
                    message=f"Duplicate component name detected: '{name}'. Each node ID must be unique.",
                    node_id=name
                ))
            else:
                node_set.add(name)
                nodes.append(name)
                step_dict[name] = s
                clean_deps = [d.strip() for d in deps if isinstance(d, str) and d.strip()]
                dep_map[name] = clean_deps

        # If fundamental node ID parsing failed with errors, return early
        if not nodes or any(i.code in (DAGErrorCode.INVALID_NODE_ID, DAGErrorCode.DUPLICATE_NODE) for i in issues):
            return DAGValidationResult(is_valid=False, issues=issues)

        # 3. Validate dependencies (missing, self-dependencies)
        # In BuildSequenceStep: step 'v' has dependency 'u' -> edge is u -> v (u executes before v)
        adj_list: Dict[str, List[str]] = {n: [] for n in nodes}
        in_degree: Dict[str, int] = {n: 0 for n in nodes}
        out_degree: Dict[str, int] = {n: 0 for n in nodes}

        for node in nodes:
            declared_deps = dep_map.get(node, [])
            for dep in declared_deps:
                if dep == node:
                    issues.append(DAGValidationIssue(
                        code=DAGErrorCode.SELF_DEPENDENCY,
                        message=f"Node '{node}' directly declares itself as a dependency.",
                        node_id=node
                    ))
                elif dep not in node_set:
                    issues.append(DAGValidationIssue(
                        code=DAGErrorCode.MISSING_DEPENDENCY,
                        message=f"Node '{node}' depends on unknown component '{dep}'.",
                        node_id=node,
                        details={"missing_dependency": dep}
                    ))
                else:
                    # Valid dependency: dep -> node
                    adj_list[dep].append(node)
                    in_degree[node] += 1
                    out_degree[dep] += 1

        # 4. Check for orphan nodes (completely disconnected in multi-node plans)
        if len(nodes) > 1:
            for node in nodes:
                if in_degree[node] == 0 and out_degree[node] == 0:
                    issues.append(DAGValidationIssue(
                        code=DAGErrorCode.ORPHAN_NODE,
                        message=f"Node '{node}' is completely disconnected (has 0 dependencies and nothing depends on it).",
                        node_id=node
                    ))

        # 5. Cycle Detection and Deterministic Topological Sort (Kahn's Algorithm)
        # Ready queue: nodes with in_degree == 0, sorted alphabetically for deterministic tie-breaking
        ready_nodes = sorted([n for n in nodes if in_degree[n] == 0])
        execution_order: List[str] = []

        while ready_nodes:
            # Deterministic selection: always pop the lexicographically smallest ready node
            curr = ready_nodes.pop(0)
            execution_order.append(curr)

            for neighbor in adj_list[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    # Insert in sorted order to maintain deterministic priority
                    ready_nodes.append(neighbor)
                    ready_nodes.sort()

        cycle_path: Optional[List[str]] = None
        if len(execution_order) < len(nodes):
            # Unprocessed nodes contain at least one directed cycle
            cycle_nodes = [n for n in nodes if in_degree[n] > 0]
            cycle_path = cls._extract_cycle_path(cycle_nodes, adj_list)
            cycle_str = " -> ".join(cycle_path) if cycle_path else " -> ".join(cycle_nodes)
            issues.append(DAGValidationIssue(
                code=DAGErrorCode.CYCLE_DETECTED,
                message=f"Circular dependency cycle detected: {cycle_str}",
                details={"cycle_path": cycle_path or cycle_nodes}
            ))

        is_valid = len(issues) == 0
        return DAGValidationResult(
            is_valid=is_valid,
            execution_order=execution_order if is_valid else [],
            issues=issues,
            cycle_path=cycle_path
        )

    @classmethod
    def _extract_cycle_path(cls, cycle_nodes: List[str], adj_list: Dict[str, List[str]]) -> List[str]:
        """Performs 3-color DFS to extract the exact directed cycle path for diagnostic feedback."""
        cycle_set = set(cycle_nodes)
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {n: WHITE for n in cycle_set}
        parent: Dict[str, Optional[str]] = {n: None for n in cycle_set}
        cycle: List[str] = []

        def dfs(u: str) -> bool:
            color[u] = GRAY
            for v in adj_list.get(u, []):
                if v not in cycle_set:
                    continue
                if color[v] == GRAY:
                    # Cycle found from v to u
                    cycle.append(v)
                    curr = u
                    while curr is not None and curr != v:
                        cycle.append(curr)
                        curr = parent.get(curr)
                    cycle.append(v)
                    cycle.reverse()
                    return True
                elif color[v] == WHITE:
                    parent[v] = u
                    if dfs(v):
                        return True
            color[u] = BLACK
            return False

        for node in cycle_nodes:
            if color[node] == WHITE:
                if dfs(node):
                    return cycle

        return cycle_nodes

    @classmethod
    def format_error_feedback(cls, result: DAGValidationResult) -> str:
        """Formats machine-readable validation issues into structured feedback for bounded LLM repair."""
        if result.is_valid:
            return "DAG Validation Passed: No errors found."

        lines = ["DAG Validation Failed with the following errors:"]
        for issue in result.issues:
            node_info = f" [Node: {issue.node_id}]" if issue.node_id else ""
            lines.append(f"- [{issue.code.value}]{node_info} {issue.message}")

        if result.cycle_path:
            lines.append(f"Cycle trace: {' -> '.join(result.cycle_path)}")

        lines.append("\nPlease correct the execution plan so all dependencies are acyclic, existing, and non-empty.")
        return "\n".join(lines)
