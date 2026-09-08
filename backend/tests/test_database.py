import os
import tempfile
import pytest
from app.core.db.storage_engine import StorageEngine
from app.core.db.profile_repo import ProfileRepository
from app.core.db.paper_repo import PaperRepository
from app.core.db.episodic_repo import EpisodicRepository
from app.core.db.chat_repo import ChatRepository
from app.core.database import ChatDatabase


@pytest.fixture
def temp_db_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ── StorageEngine Tests ───────────────────────────────────────────────────────

def test_storage_engine_atomic_write_and_read(temp_db_dir):
    db_file = os.path.join(temp_db_dir, "test_db.json")
    storage = StorageEngine(db_file)
    
    # Empty index load
    data = storage.load_index()
    assert isinstance(data, dict)
    
    # Save & reload index
    data["test_key"] = "test_value"
    storage.save_index(data)
    
    loaded = storage.load_index()
    assert loaded.get("test_key") == "test_value"


# ── ProfileRepository Tests ───────────────────────────────────────────────────

def test_profile_repository_create_and_query_user(temp_db_dir):
    db_file = os.path.join(temp_db_dir, "test_db.json")
    storage = StorageEngine(db_file)
    repo = ProfileRepository(storage)

    user = repo.create_user(email="alice@example.com", password_hash="hash123", full_name="Alice Smith")
    assert user["email"] == "alice@example.com"
    assert user["id"].startswith("usr_")

    queried = repo.get_user_by_email("alice@example.com")
    assert queried is not None
    assert queried["full_name"] == "Alice Smith"

    assert repo.get_user_by_email("nonexistent@example.com") is None


# ── PaperRepository & Hash Deduplication Tests ────────────────────────────────

def test_paper_repository_hash_deduplication(temp_db_dir):
    db_file = os.path.join(temp_db_dir, "test_db.json")
    storage = StorageEngine(db_file)
    repo = PaperRepository(storage)

    file_hash = "abc123md5hash"
    repo.save_paper_hash(file_hash=file_hash, paper_id="test_paper_1", filename="paper1.pdf", title="Attention Paper")

    # In index, check save
    data = storage.load_index()
    assert file_hash in data.get("paper_hashes", {})

    repo.delete_paper_hash("test_paper_1")
    data_after = storage.load_index()
    assert file_hash not in data_after.get("paper_hashes", {})


# ── EpisodicRepository Tests ──────────────────────────────────────────────────

def test_episodic_repository_react_memories_and_facts(temp_db_dir):
    db_file = os.path.join(temp_db_dir, "test_db.json")
    storage = StorageEngine(db_file)
    repo = EpisodicRepository(storage)

    # ReACT steps
    repo.save_episodic_react_step(
        paper_id="paper_xyz",
        query="What is the learning rate?",
        thought="Checking table 3",
        action="get_hyperparameters()",
        observation="lr=1e-4",
        answer="The learning rate is 0.0001."
    )

    mems = repo.get_episodic_react_memories(paper_id="paper_xyz")
    assert len(mems) == 1
    assert mems[0]["query"] == "What is the learning rate?"
    assert "0.0001" in mems[0]["answer_summary"]

    # User facts
    repo.save_memory_fact("Prefers PyTorch over TensorFlow", conversation_id="conv_1")
    facts = repo.get_user_facts(conversation_id="conv_1")
    assert "Prefers PyTorch over TensorFlow" in facts


# ── ChatDatabase Facade Integration Tests ─────────────────────────────────────

def test_chat_database_facade_end_to_end(temp_db_dir):
    db_file = os.path.join(temp_db_dir, "test_db.json")
    db = ChatDatabase(db_file=db_file)
    db.initialize_db()

    # Create / update conversation for paper
    cid = db.create_or_update_conversation_for_paper(
        paper_id="paper_test",
        title="Transformer Analysis",
        filename="transformer.pdf"
    )
    assert cid.startswith("conv_")
    assert db.get_active_conversation_id() == cid

    # Save user & assistant messages
    msg1 = db.save_message(conversation_id=cid, role="user", content="Explain multi-head attention")
    assert msg1["role"] == "user"

    msg2 = db.save_message(
        conversation_id=cid,
        role="assistant",
        content="Multi-head attention projects queries, keys, and values.",
        model_used="Groq Cloud (qwen3.8)",
        thought="Explaining projection matrices",
        action="vector_search(attention)",
        observation="Found 8 heads specification",
        answer="Multi-head attention projects queries, keys, and values into h subspaces."
    )
    assert msg2["role"] == "assistant"
    assert msg2["thought"] == "Explaining projection matrices"

    # Verify messages retrieval
    messages = db.get_messages(cid)
    assert len(messages) == 2

    # Verify conversations listing
    convs = db.get_all_conversations()
    assert len(convs) >= 1
    assert any(c["id"] == cid for c in convs)

    # Title update
    db.update_conversation_title(cid, "Custom Transformer Breakdown")
    convs_updated = db.get_all_conversations()
    updated_conv = next(c for c in convs_updated if c["id"] == cid)
    assert updated_conv["title"] == "Custom Transformer Breakdown"

    # Delete conversation
    assert db.delete_conversation(cid) is True
    assert db.get_active_conversation_id() is None
