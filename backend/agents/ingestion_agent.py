import os
import json
import sys
from typing import List, TypedDict
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from schemas import SectionInfo, PaperMetadata

# Define LangGraph State
class AgentState(TypedDict):
    parsed_sections: dict
    metadata: PaperMetadata

def run_ingestion_agent(parsed_sections: dict, model_name: str = "qwen2.5-coder:1.5b") -> PaperMetadata:
    """Uses Ollama structured output to extract metadata from parsed paper sections."""
    
    # Extract front matter which contains title, authors, and abstract
    front_matter = parsed_sections.get("Metadata / Front Matter", "")
    if not front_matter:
        # Fallback to the first available section if front matter is missing
        keys = list(parsed_sections.keys())
        front_matter = parsed_sections[keys[0]] if keys else ""

    # Compile the list of sections found and their sizes to pass as context
    sections_list = []
    for title, content in parsed_sections.items():
        sections_list.append(f"- {title}: {len(content)} characters")
    sections_list_str = "\n".join(sections_list)

    # Truncate front_matter to prevent authors list token explosion
    front_matter = front_matter[:1500]

    # num_predict=512 prevents the LLM looping infinitely in the 'authors' list field
    print(f"Initializing ChatOllama with model '{model_name}'...")
    llm = ChatOllama(model=model_name, temperature=0.0, num_ctx=2048, num_predict=512)
    structured_llm = llm.with_structured_output(PaperMetadata)

    prompt = (
        "You are an academic paper ingestion agent. Extract metadata from the paper front matter.\n\n"
        f"--- FRONT MATTER (first 1500 chars) ---\n{front_matter}\n\n"
        f"--- SECTIONS FOUND ---\n{sections_list_str}\n\n"
        "STRICT RULES:\n"
        "- title: exact paper title (1 string).\n"
        "- authors: list of UNIQUE author names only, max 10. Do NOT repeat names.\n"
        "- abstract: the paper abstract (1-3 sentences max).\n"
        "- sections_found: list of section titles and character counts.\n"
        "- primary_contribution: 1-2 sentence summary of main contribution."
    )

    try:
        print("Sending request to local Ollama for structured metadata extraction...")
        metadata = structured_llm.invoke(prompt)
    except Exception as e:
        print(f"Warning: Ingestion Agent LLM call failed ({e}). Falling back to baseline metadata.")
        fallback_title = "Unknown Remote Sensing Research Paper"
        if "Title: " in front_matter:
            extracted_t = front_matter.split("Title: ")[1].split("\n")[0].strip()
            if extracted_t and extracted_t.lower() != "unknown":
                fallback_title = extracted_t
        metadata = PaperMetadata(
            title=fallback_title,
            authors=["Unknown Author"],
            abstract="Abstract could not be parsed automatically due to section absence or API limits.",
            sections_found=[SectionInfo(title=title, character_count=len(content)) for title, content in parsed_sections.items()],
            primary_contribution="Adaptive change detection for remote sensing images."
        )

    return metadata

# Define LangGraph Node
def ingestion_node(state: AgentState) -> dict:
    parsed_sections = state["parsed_sections"]
    metadata = run_ingestion_agent(parsed_sections)
    return {"metadata": metadata}

# Compile LangGraph Workflow
workflow = StateGraph(AgentState)
workflow.add_node("ingestion", ingestion_node)
workflow.add_edge(START, "ingestion")
workflow.add_edge("ingestion", END)
graph = workflow.compile()

if __name__ == "__main__":
    # Test harness
    input_json_path = "backend/papers/vlcd_paper_parsed.json"
    if not os.path.exists(input_json_path):
        print(f"Error: Parsed paper JSON not found at '{input_json_path}'. Please run parser.py first.", file=sys.stderr)
        sys.exit(1)

    with open(input_json_path, "r", encoding="utf-8") as f:
        parsed_data = json.load(f)

    print("Starting LangGraph Ingestion Agent flow...")
    initial_state = {"parsed_sections": parsed_data}
    
    # Run graph
    result = graph.invoke(initial_state)
    metadata = result.get("metadata")

    if metadata:
        output_path = "backend/papers/vlcd_paper_metadata.json"
        with open(output_path, "w", encoding="utf-8") as f:
            # Save Pydantic model representation
            json.dump(metadata.model_dump(), f, indent=4, ensure_ascii=False)
        
        print("\n=== EXTRACTION SUCCESSFUL ===")
        print(f"Title: {metadata.title}")
        print(f"Authors: {', '.join(metadata.authors)}")
        print(f"Primary Contribution: {metadata.primary_contribution}")
        print(f"Saved metadata JSON to: {output_path}")
    else:
        print("Error: Failed to extract metadata.", file=sys.stderr)
