"""Phase 4.3 near-miss log unit tests."""

from src.metrics.near_miss import NearMissLog


def test_near_miss_log_trims_to_max_entries():
    log = NearMissLog(max_entries=2)
    for index in range(3):
        log.append(
            query_text=f"query-{index}",
            model="gpt-4o-mini",
            best_similarity=0.93,
            threshold=0.95,
            matched_prompt_text="seed",
        )
    entries = log.entries()
    assert len(entries) == 2
    assert entries[0].query_text == "query-1"
    assert entries[1].query_text == "query-2"


def test_near_miss_gap_and_csv_export():
    log = NearMissLog()
    log.append(
        query_text="Tell me about Python",
        model="gpt-4o-mini",
        best_similarity=0.93,
        threshold=0.95,
        matched_prompt_text="What is Python?",
    )
    row = log.to_dicts()[0]
    assert row["gap"] == 0.02
    csv_text = log.to_csv()
    assert "Tell me about Python" in csv_text
    assert "What is Python?" in csv_text
