import pytest
from app.agents.chat_agent import (
    parse_react_traces,
    clean_react_content,
    is_code_request
)


# ── parse_react_traces tests ──────────────────────────────────────────────────

def test_parse_react_traces_full():
    """Verifies parsing of complete THOUGHT, ACTION, OBSERVATION, and ANSWER trace."""
    text = (
        "THOUGHT: Analyzing the paper architecture...\n"
        "ACTION: vector_search(attention mechanism)\n"
        "OBSERVATION: Found 3 relevant sections on Multi-Head Attention.\n"
        "ANSWER: The paper uses scaled dot-product attention."
    )
    t, a, o = parse_react_traces(text)
    assert t == "Analyzing the paper architecture..."
    assert a is not None and "vector_search" in a
    assert o is not None and "Found 3 relevant sections" in o


def test_parse_react_traces_no_action_observation():
    """Verifies parsing when only THOUGHT is present without ACTION/OBSERVATION."""
    text = (
        "THOUGHT: Explaining the conceptual background of diffusion models.\n"
        "ANSWER: Diffusion models add gaussian noise iteratively."
    )
    t, a, o = parse_react_traces(text)
    assert t == "Explaining the conceptual background of diffusion models."
    assert a is None
    assert o is None


def test_parse_react_traces_alternative_tags():
    """Verifies that 'Thinking:' and 'Reasoning:' tags are handled properly."""
    text1 = (
        "Thinking: Need to verify hyperparameter settings.\n"
        "ACTION: hyperparameter_tool(learning_rate)\n"
        "OBSERVATION: lr=0.0001\n"
        "ANSWER: Learning rate is 1e-4."
    )
    t1, a1, o1 = parse_react_traces(text1)
    assert t1 == "Need to verify hyperparameter settings."
    assert "hyperparameter_tool" in a1
    assert "lr=0.0001" in o1

    text2 = (
        "Reasoning: The mathematical proofs are in Appendix B.\n"
        "ANSWER: Appendix B confirms convergence."
    )
    t2, a2, o2 = parse_react_traces(text2)
    assert t2 == "The mathematical proofs are in Appendix B."
    assert a2 is None
    assert o2 is None


def test_parse_react_traces_empty_and_unstructured():
    """Verifies that unstructured or empty text returns (None, None, None)."""
    assert parse_react_traces("") == (None, None, None)
    assert parse_react_traces("Just plain text with no ReACT trace tokens.") == (None, None, None)


def test_parse_react_traces_multiple_steps_latest():
    """Verifies that the latest THOUGHT, ACTION, and OBSERVATION are extracted when multiple occur."""
    text = (
        "THOUGHT: First step thinking.\n"
        "ACTION: tool_one()\n"
        "OBSERVATION: Result one.\n"
        "THOUGHT: Second step refined thinking.\n"
        "ACTION: tool_two()\n"
        "OBSERVATION: Result two.\n"
        "ANSWER: Done."
    )
    t, a, o = parse_react_traces(text)
    assert t == "Second step refined thinking."
    assert a == "tool_two()"
    assert o == "Result two."


# ── clean_react_content tests ─────────────────────────────────────────────────

def test_clean_react_content_extracts_answer():
    """Verifies that ANSWER: is properly isolated from prior trace tags."""
    text = "THOUGHT: thinking about the answer\nANSWER: Final answer here"
    assert clean_react_content(text) == "Final answer here"


def test_clean_react_content_with_trailing_thoughts():
    """Verifies removal of hallucinated THOUGHT/ACTION following the ANSWER: block."""
    text = (
        "THOUGHT: thinking\n"
        "ANSWER: The model uses 8 attention heads.\n"
        "THOUGHT: Should I say more?"
    )
    assert clean_react_content(text) == "The model uses 8 attention heads."


def test_clean_react_content_thought_only_fallback():
    """Verifies that thought-only output without ANSWER converts the thought to user prose."""
    text = "THOUGHT: The paper evaluates on ImageNet-1K with top-1 accuracy of 88.5%."
    cleaned = clean_react_content(text)
    assert "88.5%" in cleaned
    assert "THOUGHT:" not in cleaned


def test_clean_react_content_action_only_fallback():
    """Verifies that if text has only action syntax without thought/answer, it returns default safe prose."""
    text = "ACTION: run_eval()\nOBSERVATION: done"
    cleaned = clean_react_content(text)
    assert "I have analyzed the paper" in cleaned or "ready to help" in cleaned


def test_clean_react_content_empty_fallback():
    """Verifies that empty, None, or whitespace returns default fallback message."""
    assert clean_react_content("") == "I am ready to help you analyze your paper and write PyTorch code."
    assert clean_react_content("   \n\t  ") == "I am ready to help you analyze your paper and write PyTorch code."
    assert clean_react_content(None) == "I am ready to help you analyze your paper and write PyTorch code."


def test_clean_react_content_multiline_markdown():
    """Verifies that markdown formatting and code blocks within ANSWER: are preserved."""
    markdown_answer = (
        "THOUGHT: Formulating markdown.\n"
        "ANSWER: Here is the code:\n"
        "```python\n"
        "import torch\n"
        "x = torch.randn(1, 3, 224, 224)\n"
        "```\n"
        "Enjoy!"
    )
    cleaned = clean_react_content(markdown_answer)
    assert "```python" in cleaned
    assert "import torch" in cleaned
    assert "Enjoy!" in cleaned
    assert "THOUGHT:" not in cleaned


# ── is_code_request tests ──────────────────────────────────────────────────────

def test_is_code_request_explicit_triggers_positive():
    """Verifies detection of explicit code generation requests."""
    assert is_code_request("write pytorch code for this model") is True
    assert is_code_request("generate code for the attention layer") is True
    assert is_code_request("give me the code for training loop") is True
    assert is_code_request("show me the code of the loss function") is True
    assert is_code_request("implement in pytorch the transformer decoder") is True
    assert is_code_request("synthesize code for this architecture") is True


def test_is_code_request_negative_conceptual_questions():
    """Verifies that conceptual and analytical questions are NOT classified as code requests."""
    assert is_code_request("what is the attention mechanism?") is False
    assert is_code_request("why does the author use layer normalization?") is False
    assert is_code_request("how does the model perform on GLUE?") is False
    assert is_code_request("which dataset was used in experiments?") is False
    assert is_code_request("can you explain the latent space representation?") is False
    assert is_code_request("describe the training objective") is False


def test_is_code_request_verb_noun_combination():
    """Verifies trigger on code verb + code noun combinations."""
    assert is_code_request("write a python script for evaluation") is True
    assert is_code_request("create a pytorch class for the backbone") is True


def test_is_code_request_non_code_plain_statements():
    """Verifies that plain descriptive statements without code intent are False."""
    assert is_code_request("The paper introduces a novel regularization technique.") is False
    assert is_code_request("Table 1 summarizes accuracy across benchmarks.") is False
    assert is_code_request("This research was published at NeurIPS 2024.") is False


# ── resolve_failover_model_id tests ──────────────────────────────────────────

def test_resolve_failover_model_id_scenarios():
    """Verifies frontend model ID resolution when backend auto-failover/fallback occurs."""
    from app.agents.chat_agent import resolve_failover_model_id

    # 1. Gemini failover
    assert resolve_failover_model_id("Gemini 2.0 Flash (Auto-Failover)") == "google/gemini-2.5-flash"
    assert resolve_failover_model_id("OpenRouter (google/gemini-2.5-flash Auto-Failover)") == "google/gemini-2.5-flash"

    # 2. DeepSeek failover
    assert resolve_failover_model_id("OpenRouter (deepseek/deepseek-r1:free Auto-Failover)") == "deepseek/deepseek-r1:free"

    # 3. GPT-OSS fallback
    assert resolve_failover_model_id("Groq Cloud (openai/gpt-oss-120b Fallback)") == "openai/gpt-oss-120b"

    # 4. Groq / Qwen fallback from offline local model
    assert resolve_failover_model_id("Groq Cloud (qwen/qwen3.8-27b Fallback)") == "qwen/qwen3.8-27b"

    # 5. Normal model usage without failover returns None (must NOT disrupt user selection)
    assert resolve_failover_model_id("Groq Cloud (qwen/qwen3.8-27b)") is None
    assert resolve_failover_model_id("OpenRouter (google/gemini-2.5-flash)") is None
    assert resolve_failover_model_id("Local Ollama (qwen2.5-coder:1.5b)") is None
    assert resolve_failover_model_id("") is None
    assert resolve_failover_model_id(None) is None

