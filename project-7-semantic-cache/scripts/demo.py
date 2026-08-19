#!/usr/bin/env python3
"""Phase 6.1 — portfolio demo: miss → exact hit → semantic hit → metrics."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

DEFAULT_URL = "http://localhost:8080"
SEED_PATH = Path(__file__).resolve().parent / "seed_queries.json"


@dataclass(frozen=True)
class DemoStep:
    name: str
    prompt: str
    cache: str
    latency_ms: float
    similarity: str | None = None


def _chat(
    client: httpx.Client, *, base_url: str, payload: dict
) -> tuple[dict, dict[str, str], float]:
    started = time.perf_counter()
    response = client.post(f"{base_url.rstrip('/')}/v1/chat/completions", json=payload)
    latency_ms = (time.perf_counter() - started) * 1000
    response.raise_for_status()
    headers = {key.lower(): value for key, value in response.headers.items()}
    return response.json(), headers, latency_ms


def _metric_value(metrics_text: str, name: str, **labels: str) -> float | None:
    for line in metrics_text.splitlines():
        if not line.startswith(name):
            continue
        if labels and not all(f'{key}="{value}"' in line for key, value in labels.items()):
            continue
        parts = line.rsplit(" ", 1)
        if len(parts) != 2:
            continue
        try:
            return float(parts[1])
        except ValueError:
            continue
    return None


def run_demo(*, base_url: str, seed_path: Path) -> list[DemoStep]:
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    group = next(
        (item for item in seed["groups"] if item and "semantic cach" in item[0].lower()),
        seed["groups"][0],
    )
    fresh_prompt = group[0]
    exact_prompt = group[0]
    paraphrase_prompt = group[1]

    payload_base = {
        "model": seed.get("model", "gpt-4o-mini"),
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": seed["system_prompt"]},
            {"role": "user", "content": ""},
        ],
    }

    steps: list[DemoStep] = []
    with httpx.Client(timeout=30.0) as client:
        for name, prompt in [
            ("1. Fresh query (MISS)", fresh_prompt),
            ("2. Exact repeat (HIT)", exact_prompt),
            ("3. Paraphrase (semantic HIT)", paraphrase_prompt),
        ]:
            payload = {
                **payload_base,
                "messages": [
                    payload_base["messages"][0],
                    {"role": "user", "content": prompt},
                ],
            }
            _, headers, latency_ms = _chat(client, base_url=base_url, payload=payload)
            steps.append(
                DemoStep(
                    name=name,
                    prompt=prompt,
                    cache=headers.get("x-cache", "MISS"),
                    latency_ms=latency_ms,
                    similarity=headers.get("x-cache-similarity"),
                )
            )
    return steps


def print_steps(steps: list[DemoStep]) -> None:
    print("\n=== Semantic Cache Demo ===\n")
    for step in steps:
        similarity = f"  similarity={step.similarity}" if step.similarity else ""
        print(f"{step.name}")
        print(f"  prompt: {step.prompt!r}")
        print(f"  X-Cache: {step.cache}  latency: {step.latency_ms:.1f} ms{similarity}\n")


def print_metrics_snapshot(base_url: str) -> None:
    response = httpx.get(f"{base_url.rstrip('/')}/metrics", timeout=10.0)
    response.raise_for_status()
    metrics = response.text
    hits = _metric_value(metrics, "cache_requests_total", result="hit", model="gpt-4o-mini") or 0.0
    misses = (
        _metric_value(metrics, "cache_requests_total", result="miss", model="gpt-4o-mini") or 0.0
    )
    tokens_saved = _metric_value(metrics, "cache_tokens_saved_total", model="gpt-4o-mini") or 0.0
    active_entries = _metric_value(metrics, "cache_entries_active") or 0.0
    total = hits + misses
    hit_rate = (hits / total * 100) if total else 0.0
    print("=== Prometheus snapshot ===")
    print(f"  hit rate: {hit_rate:.1f}% ({int(hits)} hits / {int(total)} requests)")
    print(f"  tokens saved (est.): {int(tokens_saved)}")
    print(f"  active cache entries: {int(active_entries)}")


def print_grafana_hints() -> None:
    print("\n=== Grafana (open while recording) ===")
    print("  Dashboard → http://localhost:3000/d/semantic-cache-overview")
    print("  Login     → admin / admin")
    print("  Watch: Hit Rate, Tokens Saved, Request Latency panels climb during load test.\n")


def maybe_run_load_test(*, base_url: str, requests: int, concurrency: int) -> None:
    script = Path(__file__).resolve().parent / "load_test.py"
    print(f"=== Running load test ({requests} requests) to populate Grafana ===\n")
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--url",
            base_url,
            "--requests",
            str(requests),
            "--concurrency",
            str(concurrency),
        ],
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Portfolio demo for semantic cache proxy.")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--seed-file", type=Path, default=SEED_PATH)
    parser.add_argument(
        "--load-test", action="store_true", help="Run load test after the 3-step demo"
    )
    parser.add_argument("--requests", type=int, default=2000, help="Load test request count")
    parser.add_argument("--concurrency", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    steps = run_demo(base_url=args.url, seed_path=args.seed_file)
    print_steps(steps)
    print_metrics_snapshot(args.url)
    print_grafana_hints()
    if args.load_test:
        maybe_run_load_test(base_url=args.url, requests=args.requests, concurrency=args.concurrency)
        print_metrics_snapshot(args.url)


if __name__ == "__main__":
    main()
