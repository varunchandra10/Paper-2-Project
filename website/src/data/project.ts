export interface WorkflowStage {
  id: number;
  name: string;
  tagline: string;
  description: string;
  output: string;
}

export interface FeatureItem {
  id: string;
  title: string;
  description: string;
  category: string;
  highlight: string;
}

export interface TechItem {
  name: string;
  role: string;
  note: string;
}

export interface TechGroup {
  category: string;
  items: TechItem[];
}

export interface DemoChapter {
  time: string;
  seconds: number;
  title: string;
  description: string;
}

export const project = {
  name: "RUEXIS AI",
  acronym: "Research → Understand → Extract → Execute → Implement → Synthesize",
  descriptor: "Autonomous Multi-Agent Research-to-Code Compiler",
  headline: "From research papers to executable systems.",
  supportingCopy:
    "RUEXIS AI analyzes research papers, extracts methodology and implementation details, organizes the work into a structured pipeline, synthesizes PyTorch code, and validates generated syntax.",
  links: {
    github: "https://github.com/varunchandra10/Paper-2-Project",
    demo: "#demo",
    workflow: "#workflow",
    features: "#features",
    architecture: "#architecture",
  },
  evidence: [
    {
      metric: "48",
      label: "Research Papers",
      detail: "Evaluated across computer vision, NLP, and multimodal architectures",
    },
    {
      metric: "332",
      label: "PyTorch Files",
      detail: "Structured modular components including models, losses, and datasets",
    },
    {
      metric: "~24K",
      label: "Lines of Code",
      detail: "Synthesized clean, documented PyTorch implementations",
    },
    {
      metric: "100%",
      label: "AST Syntax Validity",
      detail: "Validated through Python AST parsing across evaluated test set",
      note: "AST syntax validity proves Python syntax, not guaranteed reproducibility.",
    },
  ],
  problemSolution: {
    heading: "Research is readable. Reproduction is the hard part.",
    problem: {
      title: "The Reproduction Bottleneck",
      description:
        "Research papers often distribute implementation details across equations, diagrams, experimental appendices, and unstated assumptions. Translating those scattered fragments into maintainable, executable code requires intense manual effort.",
      points: [
        "Equations omitted from main text and hidden in supplementary appendices",
        "Unstated hyperparameters, initialization bounds, and tensor shape contracts",
        "Ambiguous architectural nuances that block standalone implementation",
        "VRAM budget explosions from unaccounted cache and batch constraints",
      ],
    },
    solution: {
      title: "The RUEXIS Pipeline",
      description:
        "RUEXIS AI organizes research paper translation into explicit, auditable stages. From methodology extraction to hardware feasibility checks, staged PyTorch code synthesis, and syntax verification.",
      points: [
        "Structured AST extraction of mathematical operations and module contracts",
        "Feasibility profiling checking compute bounds and VRAM allocation",
        "Multi-agent code generation mapping paper components to clean PyTorch modules",
        "Automated syntax validation ensuring zero syntax or import parse errors",
      ],
    },
  },
  workflowStages: [
    {
      id: 1,
      name: "Ingest",
      tagline: "PDF & Appendix Parser",
      description: "Accepts research paper PDFs, figures, mathematical formulas, and supplementary text.",
      output: "Structured Markdown & Math AST",
    },
    {
      id: 2,
      name: "Understand",
      tagline: "Methodology Identification",
      description: "Identifies core tasks, proposed algorithmic novelties, loss formulations, and baselines.",
      output: "Methodology Specification",
    },
    {
      id: 3,
      name: "Extract",
      tagline: "Parameter & Shape Mapping",
      description: "Extracts hyperparameters, tensor shapes, activation functions, and layer dimensions.",
      output: "Component Contract Schema",
    },
    {
      id: 4,
      name: "Assess Feasibility",
      tagline: "Resource & VRAM Profiler",
      description: "Profiles compute bounds, identifies unstated assumptions, and warns of memory limits.",
      output: "Feasibility Report & Warnings",
    },
    {
      id: 5,
      name: "Plan Implementation",
      tagline: "Architecture Blueprint",
      description: "Maps paper components to modular Python files: models, datasets, losses, and utils.",
      output: "Project Directory Blueprint",
    },
    {
      id: 6,
      name: "Synthesize Code",
      tagline: "PyTorch Generation",
      description: "Specialized code agents synthesize standard PyTorch modules with idiomatic typing.",
      output: "Modular PyTorch Python Code",
    },
    {
      id: 7,
      name: "Validate",
      tagline: "AST Syntax & Import Check",
      description: "Runs 12-stage Python AST parsing, import resolution, and static syntax verification.",
      output: "Syntax Verification Report",
    },
    {
      id: 8,
      name: "Review Output",
      tagline: "Artifact Delivery",
      description: "Presents structured implementation workspace, assumption notes, and run instructions.",
      output: "Ready-to-Inspect Workspace",
    },
  ] as WorkflowStage[],
  features: [
    {
      id: "agentic-orchestration",
      title: "Staged Agentic Workflow",
      category: "Orchestration",
      description:
        "Orchestrates specialized agents across analysis, extraction, planning, and code synthesis rather than relying on a single monolithic prompt.",
      highlight: "8 Specialized Stages",
    },
    {
      id: "feasibility-profiling",
      title: "Hardware Feasibility Checks",
      category: "Analysis",
      description:
        "Profiles model tensor sizes and activation memory to identify unstated parameters and flag potential VRAM bottlenecks early.",
      highlight: "Memory & Shape Bounds",
    },
    {
      id: "pytorch-synthesis",
      title: "Modular PyTorch Synthesis",
      category: "Synthesis",
      description:
        "Generates clean, idiomatic PyTorch modules with typed forward methods, custom layers, and standard training loops.",
      highlight: "Modular File Hierarchy",
    },
    {
      id: "ast-validation",
      title: "AST Syntax Verification",
      category: "Verification",
      description:
        "Parses synthesized files through Python's native Abstract Syntax Tree compiler to guarantee zero syntax or import tree failures.",
      highlight: "100% AST Syntax Checks",
    },
    {
      id: "local-retrieval",
      title: "Local Semantic Retrieval",
      category: "Knowledge Base",
      description:
        "Indexes papers and documentation locally with FAISS vector embeddings and NetworkX relationship graphs for reliable grounding.",
      highlight: "Private & Local Index",
    },
    {
      id: "multi-model-router",
      title: "Multi-Provider Model Routing",
      category: "Inference",
      description:
        "Routes extraction, reasoning, and synthesis queries across local Ollama instances, OpenRouter, Anthropic, or OpenAI endpoints.",
      highlight: "Automatic Failover",
    },
  ] as FeatureItem[],
  demoChapters: [
    {
      time: "00:00",
      seconds: 0,
      title: "Overview",
      description: "What RUEXIS AI does and its core multi-agent architecture.",
    },
    {
      time: "00:15",
      seconds: 15,
      title: "Paper Ingestion",
      description: "Selecting a paper and parsing equations, text, and tables.",
    },
    {
      time: "00:35",
      seconds: 35,
      title: "Methodology Extraction",
      description: "Extracting hyperparameters, tensor shapes, and implementation plan.",
    },
    {
      time: "01:05",
      seconds: 65,
      title: "Code Synthesis",
      description: "Synthesizing modular PyTorch architecture, forward passes, and utils.",
    },
    {
      time: "01:45",
      seconds: 105,
      title: "AST Syntax Validation",
      description: "Inspecting verification results, syntax checks, and known caveats.",
    },
    {
      time: "02:10",
      seconds: 130,
      title: "Repository & Source",
      description: "Accessing synthesized code and reviewing setup instructions.",
    },
  ] as DemoChapter[],
  architecture: {
    heading: "A structured pipeline, not a single prompt.",
    subheading:
      "RUEXIS AI separates local orchestration, retrieval, and code generation into explicit layers with auditable data boundaries.",
    layers: [
      {
        name: "Presentation Layer",
        tech: "Desktop Companion (Electron & Next.js)",
        description: "Local desktop interface displaying paper structure, live agent traces, and generated files.",
        color: "#38BDF8",
      },
      {
        name: "Orchestration & State Engine",
        tech: "Python LangGraph Workflow Engine",
        description: "Staged execution graph coordinating agent transitions, state persistence, and fallbacks.",
        color: "#DA7756",
      },
      {
        name: "Specialized Agent Pipeline",
        tech: "8 Focused Domain Agents",
        description: "Ingest, Understand, Extract, Feasibility, Plan, Synthesize, Validate, and Review.",
        color: "#818CF8",
      },
      {
        name: "Local Knowledge & Retrieval",
        tech: "FAISS Vector Store + NetworkX Graph",
        description: "Local document embeddings and concept dependency graph for accurate section retrieval.",
        color: "#34D399",
      },
      {
        name: "Code Engine & Verifier",
        tech: "PyTorch Generator + Python AST Parser",
        description: "File tree generation, code formatting, and strict AST syntax validation pipeline.",
        color: "#FBBF24",
      },
      {
        name: "Provider Gateway",
        tech: "Local Ollama / OpenRouter / Anthropic / OpenAI",
        description: "Flexible model routing with local-first privacy options and automatic provider failover.",
        color: "#F4F3EE",
      },
    ],
  },
  techStack: [
    {
      category: "Application & Desktop",
      items: [
        { name: "Next.js & React", role: "UI Framework", note: "Server components, fast client hydration" },
        { name: "TypeScript", role: "Type Safety", note: "Strict typing across component tree" },
        { name: "Tailwind CSS", role: "Styling", note: "Claude Warm Atelier custom design tokens" },
        { name: "Electron", role: "Desktop Shell", note: "Local-first desktop execution environment" },
      ],
    },
    {
      category: "Orchestration & Backend",
      items: [
        { name: "Python 3.11+", role: "Core Runtime", note: "High-performance asynchronous backend" },
        { name: "LangGraph", role: "Agent Graph", note: "Stateful multi-agent execution pipeline" },
        { name: "Pydantic", role: "Data Contracts", note: "Strict validation schemas for paper metadata" },
      ],
    },
    {
      category: "Retrieval & Indexing",
      items: [
        { name: "FAISS", role: "Vector Search", note: "Fast local similarity search for paper chunks" },
        { name: "NetworkX", role: "Concept Graph", note: "Paper dependency and entity relationship graph" },
        { name: "NumPy", role: "Numerical Ops", note: "Vector calculations and embedding transformations" },
      ],
    },
    {
      category: "Synthesis & Verification",
      items: [
        { name: "PyTorch", role: "Target Framework", note: "Standard target library for generated neural nets" },
        { name: "Python AST", role: "Syntax Parser", note: "Abstract Syntax Tree parsing for 100% valid code" },
        { name: "Ruff", role: "Linter & Formatter", note: "Static code hygiene and style adherence" },
      ],
    },
  ] as TechGroup[],
  limitations: [
    {
      title: "Syntax vs. Functional Correctness",
      description:
        "AST syntax verification guarantees that the generated code parses into a valid Python syntax tree without compiler errors. It does not prove runtime convergence, numerical equivalence, or benchmark accuracy.",
    },
    {
      title: "Paper Ambiguity & Missing Details",
      description:
        "Many research papers omit exact initialization constants, batch sizes, or supplementary algorithms. RUEXIS notes these assumptions explicitly, but manual domain review remains essential.",
    },
    {
      title: "Isolated Execution Environment",
      description:
        "All generated PyTorch implementations should be evaluated inside an isolated virtual environment, Docker container, or sandbox before running on production hardware or cluster compute.",
    },
    {
      title: "Data Privacy & Cloud Providers",
      description:
        "When configured with cloud model providers (Anthropic, OpenAI, OpenRouter), paper excerpts and prompts are transmitted to external APIs. For fully air-gapped workflows, use local Ollama models.",
    },
  ],
};
