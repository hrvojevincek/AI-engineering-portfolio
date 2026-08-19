"""Phase 5 load test helper tests."""

from scripts.load_test import LoadTestReport, RequestSample, choose_prompt, summarize


def test_summarize_hit_rate_and_latency():
    samples = [
        RequestSample("a", "HIT", 0.010),
        RequestSample("b", "HIT", 0.012),
        RequestSample("c", "MISS", 0.120),
        RequestSample("d", "MISS", 0.150),
    ]
    report = summarize(samples, duration_seconds=2.0)
    assert report.total_requests == 4
    assert report.hits == 2
    assert report.misses == 2
    assert report.hit_rate == 0.5
    assert report.hit_latency_p50_ms == 11.0
    assert report.miss_latency_p50_ms == 135.0
    assert report.requests_per_second == 2.0


def test_choose_prompt_repeat_uses_canonical_phrase():
    groups = [["What is Python?", "Explain Python to me"], ["What is Redis?", "Explain Redis"]]
    unique = ["Write a haiku"]
    for _ in range(20):
        prompt = choose_prompt(groups, unique, repeat_ratio=1.0, paraphrase_ratio=0.0)
        assert prompt in {"What is Python?", "What is Redis?"}


def test_choose_prompt_paraphrase_skips_canonical():
    groups = [["What is Python?", "Explain Python to me"], ["What is Redis?", "Explain Redis"]]
    unique = ["Write a haiku"]
    for _ in range(20):
        prompt = choose_prompt(groups, unique, repeat_ratio=0.0, paraphrase_ratio=1.0)
        assert prompt in {"Explain Python to me", "Explain Redis"}


def test_report_to_dict():
    report = LoadTestReport(
        total_requests=10,
        hits=7,
        misses=3,
        hit_rate=0.7,
        latency_p50_ms=12.0,
        latency_p95_ms=40.0,
        hit_latency_p50_ms=10.0,
        hit_latency_p95_ms=18.0,
        miss_latency_p50_ms=35.0,
        miss_latency_p95_ms=80.0,
        duration_seconds=1.5,
        requests_per_second=6.67,
    )
    payload = report.to_dict()
    assert payload["hit_rate"] == 0.7
    assert payload["hit_latency_p95_ms"] == 18.0
    assert payload["total_requests"] == 10
