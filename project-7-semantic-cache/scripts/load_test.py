#!/usr/bin/env python3
"""Phase 5.2 — load test the semantic cache proxy."""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

DEFAULT_SEED_PATH = Path(__file__).resolve().parent / "seed_queries.json"
DEFAULT_PAYLOAD = {
    "model": "gpt-4o-mini",
    "temperature": 0.0,
}


@dataclass(frozen=True)
class RequestSample:
    prompt: str
    cache_header: str
    latency_seconds: float


@dataclass
class LoadTestReport:
    total_requests: int
    hits: int
    misses: int
    hit_rate: float
    latency_p50_ms: float
    latency_p95_ms: float
    hit_latency_p50_ms: float
    hit_latency_p95_ms: float
    miss_latency_p50_ms: float
    miss_latency_p95_ms: float
    duration_seconds: float
    requests_per_second: float

    def to_dict(self) -> dict[str, float | int]:
        return {
            "total_requests": self.total_requests,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hit_rate, 4),
            "latency_p50_ms": round(self.latency_p50_ms, 2),
            "latency_p95_ms": round(self.latency_p95_ms, 2),
            "hit_latency_p50_ms": round(self.hit_latency_p50_ms, 2),
            "hit_latency_p95_ms": round(self.hit_latency_p95_ms, 2),
            "miss_latency_p50_ms": round(self.miss_latency_p50_ms, 2),
            "miss_latency_p95_ms": round(self.miss_latency_p95_ms, 2),
            "duration_seconds": round(self.duration_seconds, 2),
            "requests_per_second": round(self.requests_per_second, 2),
        }


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * pct
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def load_seed(seed_path: Path) -> dict:
    return json.loads(seed_path.read_text(encoding="utf-8"))


def choose_prompt(
    groups: list[list[str]],
    unique_queries: list[str],
    *,
    repeat_ratio: float,
    paraphrase_ratio: float,
) -> str:
    roll = random.random()
    if roll < repeat_ratio:
        return random.choice([group[0] for group in groups])
    if roll < repeat_ratio + paraphrase_ratio:
        paraphrases = [phrase for group in groups for phrase in group[1:]]
        return random.choice(paraphrases or [group[0] for group in groups])
    base = random.choice(unique_queries or [group[0] for group in groups])
    return f"Unique request {random.randint(1, 1_000_000)}: {base}"


def summarize(samples: list[RequestSample], *, duration_seconds: float) -> LoadTestReport:
    hits = sum(1 for sample in samples if sample.cache_header.upper() == "HIT")
    misses = len(samples) - hits
    latencies_ms = [sample.latency_seconds * 1000 for sample in samples]
    hit_latencies = [
        sample.latency_seconds * 1000
        for sample in samples
        if sample.cache_header.upper() == "HIT"
    ]
    miss_latencies = [
        sample.latency_seconds * 1000
        for sample in samples
        if sample.cache_header.upper() != "HIT"
    ]
    return LoadTestReport(
        total_requests=len(samples),
        hits=hits,
        misses=misses,
        hit_rate=hits / len(samples) if samples else 0.0,
        latency_p50_ms=_percentile(latencies_ms, 0.50),
        latency_p95_ms=_percentile(latencies_ms, 0.95),
        hit_latency_p50_ms=_percentile(hit_latencies, 0.50),
        hit_latency_p95_ms=_percentile(hit_latencies, 0.95),
        miss_latency_p50_ms=_percentile(miss_latencies, 0.50),
        miss_latency_p95_ms=_percentile(miss_latencies, 0.95),
        duration_seconds=duration_seconds,
        requests_per_second=len(samples) / duration_seconds if duration_seconds else 0.0,
    )


async def _send_request(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    system_prompt: str,
    prompt: str,
    model: str,
) -> RequestSample:
    payload = {
        **DEFAULT_PAYLOAD,
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    }
    started = time.perf_counter()
    response = await client.post(f"{base_url.rstrip('/')}/v1/chat/completions", json=payload)
    response.raise_for_status()
    latency = time.perf_counter() - started
    cache_header = response.headers.get("x-cache", "MISS")
    return RequestSample(prompt=prompt, cache_header=cache_header, latency_seconds=latency)


async def run_load_test(
    *,
    base_url: str,
    total_requests: int,
    concurrency: int,
    seed_path: Path,
    repeat_ratio: float,
    paraphrase_ratio: float,
) -> LoadTestReport:
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    groups = seed["groups"]
    unique_queries = seed.get("unique_queries", [])
    system_prompt = seed["system_prompt"]
    model = seed.get("model", DEFAULT_PAYLOAD["model"])
    semaphore = asyncio.Semaphore(concurrency)
    samples: list[RequestSample] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        async def worker() -> None:
            prompt = choose_prompt(
                groups,
                unique_queries,
                repeat_ratio=repeat_ratio,
                paraphrase_ratio=paraphrase_ratio,
            )
            async with semaphore:
                sample = await _send_request(
                    client,
                    base_url=base_url,
                    system_prompt=system_prompt,
                    prompt=prompt,
                    model=model,
                )
                samples.append(sample)

        started = time.perf_counter()
        await asyncio.gather(*(worker() for _ in range(total_requests)))
        duration = time.perf_counter() - started

    return summarize(samples, duration_seconds=duration)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load test the semantic cache proxy.")
    parser.add_argument("--url", default="http://localhost:8080", help="Proxy base URL")
    parser.add_argument("--requests", type=int, default=2000, help="Total requests to send")
    parser.add_argument("--concurrency", type=int, default=20, help="Concurrent in-flight requests")
    parser.add_argument("--seed-file", type=Path, default=DEFAULT_SEED_PATH)
    parser.add_argument("--repeat-ratio", type=float, default=0.35, help="Exact repeat share")
    parser.add_argument(
        "--paraphrase-ratio",
        type=float,
        default=0.35,
        help="Paraphrase share (drawn from seed groups)",
    )
    parser.add_argument("--json-out", type=Path, default=None, help="Optional report output path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = asyncio.run(
        run_load_test(
            base_url=args.url,
            total_requests=args.requests,
            concurrency=args.concurrency,
            seed_path=args.seed_file,
            repeat_ratio=args.repeat_ratio,
            paraphrase_ratio=args.paraphrase_ratio,
        )
    )
    print(json.dumps(report.to_dict(), indent=2))
    if args.json_out:
        args.json_out.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
