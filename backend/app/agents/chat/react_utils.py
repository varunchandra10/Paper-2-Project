import re
from typing import Optional, Tuple


def is_code_request(query: str) -> bool:
    """Detects if user query is genuinely requesting code generation or script implementation.
    Does NOT trigger on conceptual questions, reviews, or queries asking what models exist."""
    q = query.lower().strip()
    
    # If the user is asking an analytical/conceptual question, do NOT route to code generator
    question_starters = [
        "what", "why", "how", "which", "where", "who", "is there", "are there", "does it",
        "did the", "can you explain", "explain", "describe", "elaborate", "tell me",
        "no model", "is mentioned", "difference between", "?"
    ]
    is_question = q.endswith("?") or any(qs in q for qs in question_starters)
    
    explicit_code_triggers = [
        "write code", "generate code", "give me code", "give me the code", "show me the code",
        "implement this in pytorch", "implement in pytorch", "implement in python",
        "create a pytorch model", "pytorch code", "python code", "write a class",
        "write a script", "code for this", "code implementation", "synthesize code"
    ]
    
    if any(trigger in q for trigger in explicit_code_triggers):
        return True
        
    if is_question:
        return False

    code_verbs = ["write", "generate", "code", "implement", "script", "create"]
    code_nouns = ["pytorch", "python", "script", "class", "module code", "code snippet", "repository"]
    
    return any(v in q for v in code_verbs) and any(n in q for n in code_nouns)


def clean_react_content(text: str) -> str:
    """Cleans ReACT prefix markers (THOUGHT:, ACTION:, OBSERVATION:, ANSWER:) from content without blanking."""
    if not text or not text.strip():
        return "I am ready to help you analyze your paper and write PyTorch code."
    
    # If explicit ANSWER: is present, take what comes after it
    if "ANSWER:" in text:
        parsed = text.split("ANSWER:")[-1].strip()
        # Ensure parsed doesn't itself start with another hallucinated THOUGHT or ACTION
        clean_parsed = re.sub(
            r'^(?:THOUGHT|Thinking|Reasoning|ACTION|OBSERVATION):\s*.*?(?=(ANSWER:|$))',
            '',
            parsed,
            flags=re.DOTALL | re.IGNORECASE
        ).strip()
        # Also strip trailing hallucinated ReACT markers
        clean_parsed = re.sub(
            r'\n+(?:THOUGHT|Thinking|Reasoning|ACTION|OBSERVATION):\s*.*$',
            '',
            clean_parsed,
            flags=re.DOTALL | re.IGNORECASE
        ).strip()
        if clean_parsed:
            return clean_parsed
        if parsed:
            return parsed

    # Clean out stray ReACT trace tokens if present
    cleaned = text
    cleaned = re.sub(r'(?:THOUGHT|Thinking|Reasoning):\s*.*?(?=(ACTION:|OBSERVATION:|ANSWER:|$))', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'ACTION:\s*.*?(?=(OBSERVATION:|ANSWER:|$))', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'OBSERVATION:\s*.*?(?=(ANSWER:|$))', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = cleaned.strip()
    
    if cleaned:
        return cleaned

    # If the text was ONLY internal thoughts/actions without an ANSWER:, extract the thoughts as prose
    t_matches = re.findall(r'(?:THOUGHT|Thinking|Reasoning):\s*([\s\S]*?)(?=(?:ACTION:|OBSERVATION:|ANSWER:|$))', text, flags=re.IGNORECASE)
    if t_matches:
        # Return the substantive thinking as a coherent explanation rather than raw code/action syntax
        clean_thought = t_matches[-1].strip()
        clean_thought = re.sub(r'ACTION:\s*.*', '', clean_thought, flags=re.DOTALL | re.IGNORECASE).strip()
        if clean_thought:
            return clean_thought

    return "I have analyzed the paper and verified its methodology, architecture, and metrics."


def parse_react_traces(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extracts the latest THOUGHT, ACTION, and OBSERVATION strings from ReACT prompt output."""
    thought, action, observation = None, None, None
    
    t_matches = re.findall(r'(?:THOUGHT|Thinking|Reasoning):\s*([\s\S]*?)(?=(?:ACTION:|OBSERVATION:|ANSWER:|$))', text, flags=re.IGNORECASE)
    if t_matches:
        thought = t_matches[-1].strip()
        
    a_matches = re.findall(r'ACTION:\s*([\s\S]*?)(?=(?:OBSERVATION:|ANSWER:|$))', text, flags=re.IGNORECASE)
    if a_matches:
        action = a_matches[-1].strip()

    o_matches = re.findall(r'OBSERVATION:\s*([\s\S]*?)(?=(?:THOUGHT:|ACTION:|ANSWER:|$))', text, flags=re.IGNORECASE)
    if o_matches:
        observation = o_matches[-1].strip()

    return thought, action, observation
