import os
import json
import sys
import requests
from typing import TypedDict, List
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from schemas import ComponentGraph, Component, ParameterDetails, ExtractedParameters, ParameterGap, GapReport

# Define LangGraph State (not used directly in pipeline Orchestrator anymore, but kept for compatibility)
class GapAgentState(TypedDict):
    component_graph: ComponentGraph
    extracted_parameters: ExtractedParameters
    gap_report: GapReport

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

def run_gap_agent(
    component_graph: ComponentGraph, 
    extracted_parameters: ExtractedParameters, 
    model_name: str = "qwen2.5-coder:1.5b"
) -> GapReport:
    """Identifies missing global parameters, runs web searches, and classifies them into: EXPLICIT, DERIVABLE, MISSING, AMBIGUOUS."""
    
    # 1. Scan for missing parameters and collect them as search targets
    gaps = []
    search_context = []
    
    for field_name in extracted_parameters.__class__.model_fields.keys():
        param = getattr(extracted_parameters, field_name)
        if param.status in ["UNKNOWN", "ASSUMED"] or param.value.lower() in ["not specified", "unknown", "none"]:
            gaps.append(field_name)
            
    if gaps:
        print(f"Identified {len(gaps)} parameters requiring search/verification.")
        # Execute Tavily/Github search for top 3 missing parameters to avoid rate limits
        for idx, param_name in enumerate(gaps[:3], 1):
            query = f"VLCD change detection paper {param_name} hyperparameter"
            print(f"\n[{idx}] Searching details for gap: '{param_name}'...")
            tavily_results = search_tavily(query)
            github_results = search_github(query)
            
            context_block = (
                f"Parameter: {param_name}\n"
                f"Web Search Results:\n{tavily_results or 'No web results.'}\n"
                f"GitHub Results:\n{github_results or 'No GitHub results.'}\n"
            )
            search_context.append(context_block)
            
    search_context_str = "\n====================\n".join(search_context)

    # 2. Invoke local Ollama to classify all 11 global parameters
    # num_predict=768 prevents looping in parameter_gaps list fields
    llm = ChatOllama(model=model_name, temperature=0.0, num_ctx=4096, num_predict=768)
    structured_llm = llm.with_structured_output(GapReport)

    prompt = (
        "You are an academic project audit agent. Your task is to analyze the extracted parameters from a research paper, "
        "supplemented by web search results, and classify each parameter's status into one of:\n"
        "- 'EXPLICIT': Explicitly stated in the paper text.\n"
        "- 'DERIVABLE': Not explicitly stated, but can be derived from standard practices, baseline frameworks, or inputs (e.g. Swin Transformer patch size is usually 4).\n"
        "- 'MISSING': Completely missing from the paper and search results.\n"
        "- 'AMBIGUOUS': Stated, but described vaguely (e.g. 'learning rate is adjusted dynamically' without formula).\n\n"
        "--- CURRENT EXTRACTED PARAMETERS ---\n"
        f"{json.dumps(extracted_parameters.model_dump(), indent=2)}\n\n"
        "--- SUPPLEMENTARY WEB/CODE SEARCH RESULTS ---\n"
        f"{search_context_str}\n\n"
        "Instructions:\n"
        "1. Classify each of the 11 global parameters: model, dataset, optimizer, learning_rate, batch_size, epochs, loss, scheduler, input_size, augmentation, hardware.\n"
        "2. For each parameter, provide:\n"
        "   - 'parameter_name': The exact parameter name (matching the list above).\n"
        "   - 'classification': 'EXPLICIT', 'DERIVABLE', 'MISSING', or 'AMBIGUOUS'.\n"
        "   - 'value': The verified/resolved value of the parameter.\n"
        "   - 'details': A technical rationale or source for this classification and value.\n"
        "3. Enforce the 'has_critical_missing_parameters' flag (set to true if any critical parameter like learning_rate, optimizer, or loss is MISSING).\n"
        "4. Provide a high-level executive 'summary' of the parameter gaps."
    )

    print("\nSending context to local Ollama for structured gap classification...")
    try:
        gap_report = structured_llm.invoke(prompt)
    except Exception as e:
        print(f"Warning: Gap classification LLM call failed ({e}). Building empty fallback report.")
        fallback_gaps = []
        has_missing = False
        for field_name in extracted_parameters.__class__.model_fields.keys():
            param = getattr(extracted_parameters, field_name)
            classification = "EXPLICIT"
            if param.status == "UNKNOWN":
                classification = "MISSING"
                if field_name in ["optimizer", "learning_rate", "loss"]:
                    has_missing = True
            elif param.status == "ASSUMED":
                classification = "DERIVABLE"
            elif param.status == "INFERRED":
                classification = "DERIVABLE"
            fallback_gaps.append(ParameterGap(
                parameter_name=field_name,
                classification=classification,
                value=param.value,
                details=param.rationale
            ))
        gap_report = GapReport(
            parameter_gaps=fallback_gaps,
            has_critical_missing_parameters=has_missing,
            summary="Fallback gap report generated programmatically due to LLM invocation timeout."
        )
        
    if gap_report and gap_report.parameter_gaps:
        for g in gap_report.parameter_gaps:
            g.classification = str(g.classification).upper().strip()

    return gap_report

