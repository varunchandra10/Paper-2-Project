import os
import json
import sys
import requests
from typing import TypedDict, List
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from schemas import ComponentGraph, Component, ParameterDetails

# Define LangGraph State
class GapAgentState(TypedDict):
    component_graph: ComponentGraph

def load_dotenv():
    # Check current directory and backend directory for .env
    for path in [".env", "backend/.env"]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()
            print(f"Loaded environment variables from '{path}'")
            break

# Load environment variables on startup
load_dotenv()

def search_tavily(query: str) -> str:
    """Queries Tavily API for web search results. Falls back gracefully if no key is set."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print(f"  [Tavily] No API key found. Skipping search for query: '{query}'")
        return ""
    
    print(f"  [Tavily] Searching for: '{query}'...")
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=3)
        results = []
        for res in response.get("results", []):
            results.append(f"Title: {res.get('title')}\nSnippet: {res.get('content')}\nURL: {res.get('url')}\n")
        return "\n".join(results)
    except Exception as e:
        print(f"  [Tavily] Error during search: {e}", file=sys.stderr)
        return ""

def search_github(query: str) -> str:
    """Queries GitHub API for relevant repository descriptions/code. Safe and rate-limit aware."""
    print(f"  [GitHub] Searching repositories for: '{query}'...")
    url = f"https://api.github.com/search/repositories?q={query}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Paper-to-Project-Agent"
    }
    # Optional token to avoid rate limits
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
        
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            items = response.json().get("items", [])[:3]
            results = []
            for item in items:
                results.append(f"Repo: {item.get('full_name')}\nDesc: {item.get('description')}\nURL: {item.get('html_url')}\n")
            return "\n".join(results)
        else:
            print(f"  [GitHub] API returned status {response.status_code}")
            return ""
    except Exception as e:
        print(f"  [GitHub] Error during search: {e}", file=sys.stderr)
        return ""

def run_gap_agent(component_graph: ComponentGraph, model_name: str = "qwen2.5-coder:1.5b") -> ComponentGraph:
    """Identifies missing parameters, runs web searches, and fills gaps using local LLM reasoning."""
    
    # 1. Identify missing parameters
    gaps = []
    for component in component_graph.components:
        for param_name, details in component.parameters.items():
            if details.value.lower() in ["not specified", "unknown", "none", "null"] or details.confidence == "ASSUMED":
                gaps.append((component.name, param_name, component.description))

    if not gaps:
        print("No missing parameters or gaps identified in the component graph.")
        return component_graph

    print(f"Identified {len(gaps)} potential gaps to resolve.")
    search_context = []

    # 2. Run searches for each gap (capped at 3 searches to avoid rate limits/latency)
    for idx, (comp_name, param_name, comp_desc) in enumerate(gaps[:3], 1):
        query = f"VLCD change detection {comp_name} {param_name}"
        print(f"\n[{idx}] Resolving gap: '{param_name}' in '{comp_name}'...")
        
        tavily_results = search_tavily(query)
        github_results = search_github(query)
        
        context_block = (
            f"Component: {comp_name}\n"
            f"Parameter: {param_name}\n"
            f"Description: {comp_desc}\n"
            f"Web Search Results:\n{tavily_results or 'No web results.'}\n"
            f"GitHub Results:\n{github_results or 'No GitHub results.'}\n"
        )
        search_context.append(context_block)

    search_context_str = "\n====================\n".join(search_context)

    # 3. Invoke LLM to tag parameters
    llm = ChatOllama(model=model_name, temperature=0.0)
    structured_llm = llm.with_structured_output(ComponentGraph)

    prompt = (
        "You are an expert machine learning engineer tasked with filling in the missing hyperparameters (gaps) in a component graph.\n\n"
        "Here is the current Component Graph:\n"
        f"{json.dumps(component_graph.model_dump(), indent=2)}\n\n"
        "Here are the web and code search results we found for the missing parameters:\n"
        f"{search_context_str}\n\n"
        "Instructions:\n"
        "1. For each parameter in the graph, review its current value.\n"
        "2. If the value is 'Not specified' or confidence is 'ASSUMED', use the search results above to find the correct value.\n"
        "3. Update the parameters using the following rules:\n"
        "   - Set 'confidence' to 'CONFIRMED' if you found the exact value in the search results or if it is explicitly stated in the VLCD paper context.\n"
        "   - Set 'confidence' to 'INFERRED' if the value is not explicitly stated in the search results, but you can logically deduce it from standard practices (e.g. Swin-T patch size is usually '4', standard CLIP input is '224').\n"
        "   - Set 'confidence' to 'ASSUMED' if there are no search results and you must guess a reasonable default value.\n"
        "4. Provide a clear 'rationale' explaining the source or logic behind the value and confidence selection.\n"
        "5. Leave already 'CONFIRMED' parameters unchanged.\n\n"
        "CRITICAL: Avoid placeholders like '{batch_size}' or '{width}'. Output only concrete values."
    )

    print("\nSending updated context to local Ollama for gap filling...")
    updated_graph = structured_llm.invoke(prompt)
    return updated_graph

# Compile LangGraph Workflow
def gap_finding_node(state: GapAgentState) -> dict:
    component_graph = state["component_graph"]
    updated_graph = run_gap_agent(component_graph)
    return {"component_graph": updated_graph}

workflow = StateGraph(GapAgentState)
workflow.add_node("gap_finding", gap_finding_node)
workflow.add_edge(START, "gap_finding")
workflow.add_edge("gap_finding", END)
graph = workflow.compile()
