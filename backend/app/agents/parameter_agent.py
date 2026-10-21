import json
import re
from typing import Dict, Any, Optional
from app.core.config import settings
from app.schemas.paper import PaperDocument
from app.schemas.pipeline import ExtractedParameters, ParameterDetails, ProvenanceStatus
from app.core.model_router import ModelRouter

CONFIDENCE_MAP = {
    "EXPLICIT": 95,
    "DERIVED": 85,
    "INFERRED": 70,
    "ASSUMED": 50,
    "UNKNOWN": 0
}

STRENGTH_MAP = {
    "EXPLICIT": "STRONG",
    "DERIVED": "STRONG",
    "INFERRED": "MODERATE",
    "ASSUMED": "WEAK",
    "UNKNOWN": "NONE"
}


def run_parameter_agent(
    paper_doc: Optional[PaperDocument] = None, 
    raw_text: str = "",
    model_name: str = settings.DEFAULT_MODEL
) -> ExtractedParameters:
    """
    Provenance-Aware Hyperparameter & Architecture Specification Extractor:
    Queries RAG vector database & paper text to dynamically collect ALL hyperparameter
    key-value pairs present in the paper with strict provenance attribution:
    - EXPLICIT: backed by verbatim text evidence and section coordinate.
    - DERIVED: calculated from explicit paper values with mathematical rationale.
    - INFERRED: deduced from architectural conventions or cited baselines.
    - ASSUMED: standard ML default assumed when paper is silent.
    - UNKNOWN: absent from paper (value=null, evidence_strength=NONE).
    """
    rag_context = ""
    full_text_sample = raw_text[:4000]

    if paper_doc:
        if hasattr(paper_doc, "raw_full_text") and paper_doc.raw_full_text:
            full_text_sample = paper_doc.raw_full_text[:4000]

        try:
            from app.retrieval.embeddings import generate_local_embedding
            from app.retrieval.vector_db import PaperVectorDB

            print("[Parameter Agent] Querying RAG vector DB for hyperparameter & hardware evidence...")
            rag_queries = [
                "What model architecture backbone, visual encoder, text encoder, and channel dimensions are used?",
                "What optimizer, learning rate, training batch size, epochs, weight decay, and warmup epochs are used?",
                "What loss function, learning rate scheduler, input size, spatial resolution, and dropout rate are used?",
                "What datasets, train-test split ratios, and compute hardware (GPUs, CPU, VRAM) were used?"
            ]

            vdb = PaperVectorDB()
            evidence_blocks = []
            target_p_id = getattr(paper_doc, "paper_id", None)
            for q in rag_queries:
                q_vec = generate_local_embedding(q, raise_on_failure=False)
                res = vdb.hybrid_search(query_text=q, query_vector=q_vec, top_k=2, paper_id=target_p_id)
                for item in res:
                    block = f"--- Source ({item.get('section', 'RAG')}) ---\n{item.get('content', '')}"
                    if block not in evidence_blocks:
                        evidence_blocks.append(block)

            rag_context = "\n\n".join(evidence_blocks)[:4000]
            print(f"[Parameter Agent] Grounded RAG context compiled ({len(evidence_blocks)} evidence units loaded).")
        except Exception as e:
            print(f"[Parameter Agent WARN] RAG evidence query fallback: {e}")

    prompt = f"""You are an expert ML research paper analyst. Dynamically extract ALL hyperparameters, architectural details, loss functions, training settings, hardware specs, and dataset metrics present in the paper.

--- GROUNDED PAPER CONTEXT ---
{rag_context if rag_context else full_text_sample}

STRICT PROVENANCE RULES:
1. 'EXPLICIT': Parameter is stated verbatim in the text. You MUST include the exact verbatim quote in 'evidence' and identify 'source_section'.
2. 'DERIVED': Parameter is computed or combined from multiple stated facts. Explain computation in 'rationale'.
3. 'INFERRED': Deduced from standard architecture conventions or cited baseline models.
4. 'ASSUMED': Standard community practice assumed because paper does not state it.
5. 'UNKNOWN': The paper does NOT mention this parameter. Value MUST be null, evidence MUST be null, and evidence_strength MUST be 'NONE'.
NEVER invent or fabricate parameter values as 'EXPLICIT' if they are not in the text!

EXAMPLE JSON OUTPUT FORMAT:
{{
  "parameters": {{
    "learning_rate": {{
      "value": "0.0001",
      "status": "EXPLICIT",
      "evidence": "We use the AdamW optimizer with an initial learning rate of 1e-4.",
      "source_section": "Section IV-A Implementation Details",
      "evidence_strength": "STRONG",
      "rationale": "Explicitly stated in implementation section"
    }},
    "batch_size": {{
      "value": "16",
      "status": "EXPLICIT",
      "evidence": "Models are trained with a mini-batch size of 16 images.",
      "source_section": "Section IV-A",
      "evidence_strength": "STRONG",
      "rationale": "Specified in training settings"
    }},
    "warmup_epochs": {{
      "value": null,
      "status": "UNKNOWN",
      "evidence": null,
      "source_section": null,
      "evidence_strength": "NONE",
      "rationale": "Warmup schedule not mentioned in paper text"
    }}
  }}
}}
"""

    try:
        router = ModelRouter()
        raw_res, _ = router.generate(prompt, model_id=model_name)

        json_str = raw_res
        if "```json" in raw_res:
            json_str = raw_res.split("```json")[-1].split("```")[0]
        elif "```" in raw_res:
            json_str = raw_res.split("```")[1]

        data = json.loads(json_str.strip())
        param_dict = data.get("parameters", data)

        custom_dict = {}
        primary_params = {}

        for k, v in param_dict.items():
            if not isinstance(v, dict):
                v = {"value": str(v), "status": "INFERRED"}

            raw_val = v.get("value")
            status = str(v.get("status", "UNKNOWN")).upper().strip()
            if status not in [s.value for s in ProvenanceStatus]:
                status = ProvenanceStatus.INFERRED.value

            clean_val = str(raw_val) if raw_val is not None and str(raw_val).lower() != "null" else None
            evidence = v.get("evidence")
            evidence_str = str(evidence) if evidence and str(evidence).lower() != "null" else None
            src_sec = v.get("source_section")
            src_sec_str = str(src_sec) if src_sec and str(src_sec).lower() != "null" else None
            strength = str(v.get("evidence_strength", STRENGTH_MAP.get(status, "NONE"))).upper()
            confidence = CONFIDENCE_MAP.get(status, 0.0)
            rationale = str(v.get("rationale", "Extracted from paper context"))

            # Guard against false EXPLICIT without evidence
            if status == "EXPLICIT" and (not evidence_str or clean_val is None):
                status = "INFERRED"
                strength = "MODERATE"

            p_detail = ParameterDetails(
                value=clean_val,
                confidence=confidence,
                status=status,
                evidence=evidence_str,
                source_section=src_sec_str,
                evidence_strength=strength,
                rationale=rationale,
                extraction_method="llm_rag_extraction"
            )

            k_clean = str(k).lower().strip().replace(" ", "_")
            custom_dict[k_clean] = p_detail

            if k_clean in ["learning_rate", "batch_size", "epochs", "optimizer", "loss_function", "backbone"]:
                primary_params[k_clean] = p_detail

        def _get_or_unknown(key: str, desc: str) -> ParameterDetails:
            if key in primary_params:
                return primary_params[key]
            return ParameterDetails(
                value=None,
                status=ProvenanceStatus.UNKNOWN.value,
                evidence=None,
                source_section=None,
                evidence_strength="NONE",
                confidence=0.0,
                rationale=f"{desc} was not specified in paper context",
                extraction_method="default"
            )

        extracted_obj = ExtractedParameters(
            learning_rate=_get_or_unknown("learning_rate", "Learning rate"),
            batch_size=_get_or_unknown("batch_size", "Batch size"),
            epochs=_get_or_unknown("epochs", "Training epochs"),
            optimizer=_get_or_unknown("optimizer", "Optimizer"),
            loss_function=_get_or_unknown("loss_function", "Loss function"),
            backbone=_get_or_unknown("backbone", "Model backbone"),
            custom_parameters=custom_dict
        )

        print(f"[Parameter Agent] Extracted {len(custom_dict)} parameters with verifiable provenance.")
        return extracted_obj

    except Exception as e:
        print(f"[Parameter Agent WARN] Parameter extraction fallback triggered ({e}). Returning honest UNKNOWN state.")
        return ExtractedParameters()
