#!/usr/bin/env python3
"""Detect prompt version from changed files (for CI)."""

import re
import subprocess
import sys

DEFAULT_VERSION = "1.0.0"
VERSION_RE = re.compile(r"prompts/v([\d.]+)\.ya?ml$")


def changed_prompt_versions(base_ref: str = "main") -> list[str]:
    try:
        out = subprocess.check_output(
            [
                "git",
                "diff",
                "--name-only",
                f"origin/{base_ref}...HEAD",
                "--",
                "prompts/",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        try:
            out = subprocess.check_output(
                [
                    "git",
                    "diff",
                    "--name-only",
                    "HEAD~1",
                    "HEAD",
                    "--",
                    "prompts/",
                ],
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            return [DEFAULT_VERSION]

    versions = []
    for line in out.strip().splitlines():
        match = VERSION_RE.search(line.strip())
        if match:
            versions.append(match.group(1))

    return versions or [DEFAULT_VERSION]


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "main"
    versions = changed_prompt_versions(base)
    # Use the first changed prompt; CI runs one eval per workflow
    print(versions[0])
