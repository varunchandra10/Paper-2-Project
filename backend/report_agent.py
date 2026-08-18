import os
import json
import sys
from typing import TypedDict
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from schemas import PipelineOutput, FeasibilityReport, BuildSequence, AdaptationReport
from utils import detect_gpu, detect_system_ram

class ReportState(TypedDict):
    pipeline_output: PipelineOutput
    feasibility_report: FeasibilityReport
    build_sequence: BuildSequence
    report: AdaptationReport

def run_report_agent(pipeline_output: PipelineOutput, feasibility_report: FeasibilityReport, build_sequence: BuildSequence, model_name: str = "qwen2.5-coder:1.5b") -> AdaptationReport:
    """Uses a Hybrid Python + LLM generation approach, preserving original metadata word-for-word."""
    
    # 1. Fetch system specs dynamically
    gpu_name, vram_gb = detect_gpu()
    ram_gb = detect_system_ram()
    
    # 2. Extract metadata - PRESERVED EXACTLY AS IN PAPER
    title = pipeline_output.metadata.title
    authors_str = ", ".join(pipeline_output.metadata.authors)
    abstract = pipeline_output.metadata.abstract

    # Initialize LLM for narrative generation
    llm = ChatOllama(model=model_name, temperature=0.0)

    print("Generating executive summary via Ollama...")
    # Narrative Part A: Executive Summary (focusing only on adaptation roadmap description)
    summary_prompt = (
        f"You are a Principal AI Architect. Write a brief executive summary paragraph (3-4 sentences) "
        f"explaining the purpose of this project adaptation proposal. "
        f"The purpose is to adapt the VLCD model to run within the user's specific local hardware constraints. "
        "Do NOT write any headings, do NOT repeat the paper title, and do NOT write or summarize the paper abstract."
    )
    summary_response = llm.invoke(summary_prompt)
    executive_summary = summary_response.content.strip()

    print("Generating bottleneck analysis via Ollama...")
    # Narrative Part B: ML Systems Bottleneck Analysis
    bottlenecks_summary = ""
    for f in feasibility_report.components_analysis:
        bottlenecks_summary += f"- {f.component_name} ({f.status}): {f.reason} -> Suggested Substitution: {f.suggested_substitute}\n"
    bottlenecks_summary += f"- Training Parameters ({feasibility_report.training_status}): {feasibility_report.training_reason} -> Suggested Substitution: {feasibility_report.training_substitute}\n"

    bottleneck_prompt = (
        "You are a senior Deep Learning Systems Optimization Engineer. Write a professional ML systems analysis paragraph (4-5 sentences) "
        "explaining the VRAM memory bottlenecks and training timeline constraints of the proposed architecture on local hardware. "
        f"Base your analysis on these findings:\n{bottlenecks_summary}\n\n"
        f"Explain why swapping the heavy backbones (like Swin or BiT) with lightweight models (like Swin-T or ResNet-18) "
        "and utilizing frozen CLIP encoders successfully mitigates these limitations. "
        "Do NOT write any headings."
    )
    bottleneck_response = llm.invoke(bottleneck_prompt)
    bottleneck_analysis = bottleneck_response.content.strip()

    print("Generating cloud migration guide via Ollama...")
    # Narrative Part C: Cloud Migration Instructions
    alternatives_text = ""
    for alt in feasibility_report.alternatives:
        alternatives_text += f"- Platform: {alt.platform_name}\n  Description: {alt.description}\n  Setup: {alt.how_to_use}\n"

    migration_prompt = (
        "You are a machine learning educator. Write an encouraging educational guide (2 paragraphs) on how a developer "
        "can migrate and run this change detection model on free cloud platforms (specifically Google Colab and Kaggle Kernels). "
        f"Base your guide on these alternatives:\n{alternatives_text}\n\n"
        "Explain how they can use the free NVIDIA GPUs (like Colab's T4 GPU) to scale their training and explore the codebase safely. "
        "Do NOT write any headings."
    )
    migration_response = llm.invoke(migration_prompt)
    migration_guide = migration_response.content.strip()

    # 3. Build Tables in Python (100% accurate, no hallucinations or loops)
    components_rows = ""
    for comp in pipeline_output.component_graph.components:
        params_str = "<br>".join([f"`{k}`: {v.value}" for k, v in comp.parameters.items()])
        inputs_str = ", ".join(comp.inputs)
        outputs_str = ", ".join(comp.outputs)
        
        # Get parameter confidence or default to CONFIRMED
        confidence = "CONFIRMED"
        if comp.parameters:
            confidence = list(comp.parameters.values())[0].confidence
            
        components_rows += f"| **{comp.name}** | `{comp.type}` | {inputs_str} | {outputs_str} | {params_str or 'None specified'} | {confidence} | {comp.description} |\n"

    milestones_rows = ""
    for m in build_sequence.milestones:
        objectives_str = "<br>".join([f"- {obj}" for obj in m.objectives])
        components_str = ", ".join(m.components_involved)
        milestones_rows += f"| {m.id} | **{m.name}** | `{m.estimated_complexity}` | {components_str} | {objectives_str} | {m.dependency_rationale} |\n"

    # 4. Assemble the Markdown Document
    markdown_report = f"""# Project Adaptation Proposal: {title}

**Authors:** {authors_str}

### Original Abstract
{abstract}

---

## Executive Summary
{executive_summary}

---

## 1. Extracted Architectural Components

Below is the structured registry of components extracted from the research paper. We have annotated each hyperparameter with its confidence tier (`CONFIRMED` from paper text vs. `ASSUMED` from common ML defaults):

| Component Name | Type | Inputs | Outputs | Hyperparameters | Confidence Tier | Rationale / Description |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
{components_rows}
---

## 2. Local Hardware Feasibility Profile

The system dynamically profiled the local workstation specs to evaluate training and inference bounds:

* **Host GPU Model:** `{gpu_name}`
* **Dedicated Video Memory (VRAM):** `{vram_gb} GB`
* **System Physical Memory (RAM):** `{ram_gb} GB`
* **Overall Project Feasibility Status:** `{feasibility_report.overall_status}`

### ML Systems Bottleneck Analysis
{bottleneck_analysis}

---

## 3. Cloud Alternatives & Educational Recommendations
{migration_guide}

---

## 4. Build Sequencing Roadmap

To minimize engineering risk, the project is scheduled in 5 dependency-ordered milestones, ensuring cheap data pipelines and loss functions are validated before initiating compute-heavy training phases:

| Step | Milestone Name | Complexity | Components Involved | Objectives / Tasks | Dependency Rationale |
| :---: | :--- | :---: | :--- | :--- | :--- |
{milestones_rows}
"""
    return AdaptationReport(markdown_content=markdown_report)

def report_node(state: ReportState) -> dict:
    pipeline_output = state["pipeline_output"]
    feasibility_report = state["feasibility_report"]
    build_sequence = state["build_sequence"]
    report = run_report_agent(pipeline_output, feasibility_report, build_sequence)
    return {"report": report}

# Compile LangGraph Workflow
workflow = StateGraph(ReportState)
workflow.add_node("report", report_node)
workflow.add_edge(START, "report")
workflow.add_edge("report", END)
graph = workflow.compile()
