from __future__ import annotations

from memory.memory_store import MemoryStore


def test_memory_store_adds_and_queries_interactions(tmp_path):
    store = MemoryStore(tmp_path)
    store.add_interaction("Architect", "In Progress", "Create the architecture note for the mage.")
    store.add_interaction("Developer", "In Progress", "Implement the mage class.")

    matches = store.query_memory("mage architecture", top_k=2)

    assert matches
    assert matches[0]["role"] == "Architect"


def test_memory_store_records_metrics(tmp_path):
    store = MemoryStore(tmp_path)
    metric_id = store.record_metric(
        role="Developer",
        state="In Progress",
        event_type="produce_artifact",
        latency_ms=12.5,
        success=True,
        token_usage={"input_tokens": 10},
        metadata={"hook": "post_task"},
    )

    assert metric_id > 0
