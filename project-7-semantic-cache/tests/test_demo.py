"""Phase 6 demo helper tests."""

from scripts.demo import _metric_value


def test_metric_value_parses_labeled_counter():
    metrics = """
# HELP cache_requests_total Cache lookup outcomes
# TYPE cache_requests_total counter
cache_requests_total{result="hit",model="gpt-4o-mini"} 42
cache_requests_total{result="miss",model="gpt-4o-mini"} 18
"""
    assert _metric_value(metrics, "cache_requests_total", result="hit", model="gpt-4o-mini") == 42.0
    assert _metric_value(metrics, "cache_requests_total", result="miss", model="gpt-4o-mini") == 18.0


def test_metric_value_returns_none_when_missing():
    assert _metric_value("cache_requests_total 1", "cache_tokens_saved_total") is None
