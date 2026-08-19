"""Phase 4.1 — Prometheus instrumentation for the semantic cache proxy."""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram


class CacheMetrics:
    """Prometheus metrics"""

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        self.registry = registry or CollectorRegistry(auto_describe=True)

        self.requests_total = Counter(
            "cache_requests_total",
            "Cache lookup outcomes",
            ["result", "model"],
            registry=self.registry,
        )
        self.lookup_latency_seconds = Histogram(
            "cache_lookup_latency_seconds",
            "Time spent on semantic cache lookup",
            registry=self.registry,
        )
        self.request_latency_seconds = Histogram(
            "cache_request_latency_seconds",
            "End-to-end proxy request latency",
            ["result", "model"],
            registry=self.registry,
        )
        self.similarity_score = Histogram(
            "cache_similarity_score",
            "Best-match cosine similarity per lookup",
            ["result"],
            buckets=(0.5, 0.7, 0.8, 0.85, 0.9, 0.92, 0.95, 0.97, 0.99, 1.0),
            registry=self.registry,
        )
        self.tokens_saved_total = Counter(
            "cache_tokens_saved_total",
            "Estimated tokens not sent to LLM on cache hits",
            ["model"],
            registry=self.registry,
        )
        self.entries_active = Gauge(
            "cache_entries_active",
            "Non-expired entries in the cache store",
            registry=self.registry,
        )
        self.near_miss_total = Counter(
            "cache_near_miss_total",
            "Lookups in the near-miss band below threshold",
            ["model"],
            registry=self.registry,
        )

    def record_lookup(self, *, latency_seconds: float) -> None:
        self.lookup_latency_seconds.observe(latency_seconds)

    def record_hit(
        self,
        *,
        model: str,
        similarity: float,
        tokens_saved: int,
        request_latency_seconds: float,
    ) -> None:
        self.requests_total.labels(result="hit", model=model).inc()
        self.similarity_score.labels(result="hit").observe(similarity)
        self.tokens_saved_total.labels(model=model).inc(max(tokens_saved, 0))
        self.request_latency_seconds.labels(result="hit", model=model).observe(
            request_latency_seconds
        )

    def record_miss(
        self,
        *,
        model: str,
        similarity: float | None,
        request_latency_seconds: float,
    ) -> None:
        self.requests_total.labels(result="miss", model=model).inc()
        if similarity is not None:
            self.similarity_score.labels(result="miss").observe(similarity)
        self.request_latency_seconds.labels(result="miss", model=model).observe(
            request_latency_seconds
        )

    def record_near_miss(self, *, model: str, similarity: float) -> None:
        self.near_miss_total.labels(model=model).inc()
        self.similarity_score.labels(result="near_miss").observe(similarity)

    def set_active_entries(self, count: int) -> None:
        self.entries_active.set(count)
