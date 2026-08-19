#!/usr/bin/env python3
"""Replay logged queries at multiple thresholds via the proxy tuner endpoint."""

from __future__ import annotations

import argparse
import json

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Call POST /v1/cache/threshold-tuner.")
    parser.add_argument("--url", default="http://localhost:8080")
    parser.add_argument(
        "--thresholds",
        default="0.90,0.95,0.98",
        help="Comma-separated similarity thresholds",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    thresholds = [float(item.strip()) for item in args.thresholds.split(",") if item.strip()]
    response = httpx.post(
        f"{args.url.rstrip('/')}/v1/cache/threshold-tuner",
        json={"thresholds": thresholds},
        timeout=30.0,
    )
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()
