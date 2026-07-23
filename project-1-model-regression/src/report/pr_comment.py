"""Format eval results as a GitHub PR comment."""

from typing import Optional

from src.models import EvalRun, RunComparison, Severity

SEVERITY_EMOJI = {
    Severity.PASS: "✅",
    Severity.WARN: "⚠️",
    Severity.CRITICAL: "❌",
}


def format_pr_comment(
    run: EvalRun,
    comparison: Optional[RunComparison] = None,
    report_url: Optional[str] = None,
) -> str:
    passed = sum(c.passed for c in run.case_results)
    total = len(run.case_results)
    lines = [
        "## Model Eval Results",
        "",
        f"**Pass rate:** {run.pass_rate:.1%} ({passed}/{total})",
        f"**Prompt:** v{run.prompt_version} · **Model:** {run.model}",
        f"**Run ID:** `{run.run_id}`",
    ]

    if comparison:
        emoji = SEVERITY_EMOJI.get(comparison.severity, "ℹ️")
        delta = comparison.pass_rate_delta * 100
        lines.extend(
            [
                "",
                f"### {emoji} Severity: **{comparison.severity.value.upper()}**",
                f"- Pass rate delta: **{delta:+.1f}%** vs baseline `{comparison.baseline_run_id}`",
                f"- Regressions: **{len(comparison.regressions)}** · Improvements: **{len(comparison.improvements)}**",
            ]
        )

        if comparison.regressions:
            lines.extend(
                ["", "<details>", "<summary>Regressed cases</summary>", ""]
            )
            for flip in comparison.regressions[:15]:
                b, c = flip.baseline, flip.current
                lines.append(
                    f"- `{flip.case_id}`: "
                    f"cat {'✓' if b.category_match else '✗'}→{'✓' if c.category_match else '✗'}, "
                    f"summary {b.summary_score}→{c.summary_score}"
                )
            if len(comparison.regressions) > 15:
                lines.append(
                    f"- _...and {len(comparison.regressions) - 15} more_"
                )
            lines.extend(["", "</details>"])

        if comparison.severity == Severity.CRITICAL:
            lines.extend(
                [
                    "",
                    "> **Merge blocked.** Pass rate dropped more than the critical threshold.",
                ]
            )
        elif comparison.severity == Severity.WARN:
            lines.extend(
                [
                    "",
                    "> Pass rate dropped more than the warn threshold. Review before merging.",
                ]
            )
    else:
        lines.extend(
            [
                "",
                "_No baseline run found — this is the first eval in the database._",
            ]
        )

    if report_url:
        lines.extend(["", f"📄 [Full HTML report]({report_url})"])
    else:
        lines.extend(
            [
                "",
                "_Download the `eval-report` workflow artifact for the full HTML diff._",
            ]
        )

    return "\n".join(lines)
