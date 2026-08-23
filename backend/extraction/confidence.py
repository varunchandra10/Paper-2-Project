from typing import Any, Optional
from schemas.canonical_paper import SourceValue, Provenance


def resolve_claim_status(
    value: Any,
    page: int,
    section: str,
    text_span: str,
    extraction_type: str
) -> SourceValue:
    """
    Standardizes and resolves the confidence status and score for extracted parameters.
    Enforces constraints (e.g. preventing elevation of UNKNOWN to EXPLICIT).
    
    extraction_type values:
    - 'explicit': Direct keyword/value matches in text.
    - 'derived': Aggregated or computed metrics.
    - 'assumed': Baseline conventions or defaulted parameters.
    - 'external': Reference bibliography lookup.
    - 'unknown': Ambiguous or uncertain extractions.
    """
    ext_lower = extraction_type.lower().strip()
    span_clean = text_span.strip() if text_span else ""

    # Rule Check: Silently converting UNKNOWN to FACT (EXPLICIT) is forbidden.
    # If the text span is empty or extraction type is unknown, status MUST be UNKNOWN.
    if ext_lower == "unknown" or not span_clean:
        status = "UNKNOWN"
        confidence = 0.0
    elif ext_lower == "explicit":
        # Direct facts must have a valid non-empty text span
        status = "EXPLICIT"
        confidence = 1.0
    elif ext_lower == "external":
        status = "EXTERNAL"
        confidence = 0.90
    elif ext_lower == "derived":
        status = "DERIVED"
        confidence = 0.85
    elif ext_lower == "assumed":
        status = "ASSUMED"
        confidence = 0.50
    else:
        status = "UNKNOWN"
        confidence = 0.0

    provenance = Provenance(
        page=page,
        section=section.strip() if section else "Unknown Section",
        text_span=span_clean
    )

    return SourceValue(
        value=value,
        source=provenance,
        status=status,
        confidence=confidence
    )


def enforce_safety_check(source_value: SourceValue) -> None:
    """
    Explicitly raises a ValueError if a client attempts to elevate an UNKNOWN claim
    into a fact (EXPLICIT) or claims high confidence (> 0.0) without a provenance span.
    """
    status = source_value.status.upper()
    confidence = source_value.confidence
    span = source_value.source.text_span.strip()

    if status == "UNKNOWN" and confidence > 0.0:
        raise ValueError(
            f"Safety Violation: Claim status is UNKNOWN but confidence is set to {confidence} (must be 0.0)."
        )

    if status == "EXPLICIT" and not span:
        raise ValueError(
            "Safety Violation: Claim status is EXPLICIT but no text span coordinates were provided."
        )

    if status == "EXPLICIT" and confidence <= 0.5:
        raise ValueError(
            f"Safety Violation: Claim status is EXPLICIT but confidence is abnormally low ({confidence})."
        )
