"""Print cost savings report from the requests audit DB."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.audit.db import get_conn  # noqa: E402
from src.audit.stats import compute_savings  # noqa: E402
from src.audit.store import fetch_all  # noqa: E402


def main() -> None:
    with get_conn() as conn:
        rows = fetch_all(conn)
        s = compute_savings(rows)

    # Headline metric first (Phase 4.3)
    print(f"COST REDUCTION: {s.saved_pct:.1f}%  (${s.saved:.6f} saved)")
    print("---")
    print(f"requests:          {s.n_requests}")
    print(f"with token counts: {s.n_with_tokens}")
    print(f"actual spend:      ${s.actual_cost:.6f}")
    print(f"baseline (gpt-4o): ${s.baseline_cost:.6f}")
    print(f"escalation rate:   {s.escalation_rate:.1%}")


if __name__ == "__main__":
    main()
