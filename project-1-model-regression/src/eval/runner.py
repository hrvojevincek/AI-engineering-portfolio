import argparse
import asyncio
from pathlib import Path
from typing import Dict, List, Optional

from src.eval.dataset import load_golden_dataset
from src.eval.diff import compare_runs, compute_category_accuracy
from src.eval.scorer import make_client, score_case
from src.eval.store import get_previous_run, save_run
from src.feature.classifier import classify_email
from src.feature.prompts import load_prompt
from src.models import (
    CaseResult,
    EvalRun,
    GoldenDataset,
    PromptConfig,
    RunComparison,
    ThresholdConfig,
)
from src.report.html import generate_html_report
from src.report.pr_comment import format_pr_comment

DEFAULT_CONCURRENCY = 10


def _build_expected_categories(dataset: GoldenDataset) -> Dict[str, str]:
    return {case.id: case.expected.category.value for case in dataset.cases}


def _aggregate(
    run_results: List[CaseResult],
    expected_categories: Dict[str, str],
    prompt_version: str,
    model: str,
) -> EvalRun:
    passed = sum(1 for r in run_results if r.passed)
    pass_rate = passed / len(run_results) if run_results else 0.0
    avg_latency = sum(r.latency_ms for r in run_results) / len(run_results)
    total_tokens = sum(r.tokens_in + r.tokens_out for r in run_results)

    run = EvalRun(
        prompt_version=prompt_version,
        model=model,
        case_results=run_results,
        pass_rate=pass_rate,
        category_accuracy={},
        avg_latency_ms=avg_latency,
        total_tokens=total_tokens,
    )
    run.category_accuracy = compute_category_accuracy(run, expected_categories)
    return run


async def run_eval(
    config: PromptConfig,
    dataset: GoldenDataset,
    thresholds: Optional[ThresholdConfig] = None,
    concurrency: int = DEFAULT_CONCURRENCY,
    skip_judge: bool = False,
) -> EvalRun:
    thresholds = thresholds or ThresholdConfig.from_env()
    expected_categories = _build_expected_categories(dataset)
    client = make_client()
    semaphore = asyncio.Semaphore(concurrency)

    async def _eval_case(case):
        async with semaphore:
            output = await classify_email(case.input, config, client=client)
            return await score_case(
                case=case,
                actual=output.result,
                latency_ms=output.latency_ms,
                tokens_in=output.tokens_in,
                tokens_out=output.tokens_out,
                client=client,
                thresholds=thresholds,
                skip_judge=skip_judge,
            )

    results = await asyncio.gather(*[_eval_case(c) for c in dataset.cases])

    run = _aggregate(
        list(results), expected_categories, config.version, config.model
    )
    return run


def _print_summary(run: EvalRun, comparison=None) -> None:
    print(f"\n{'=' * 50}")
    print(f"Run {run.run_id}")
    print(f"Prompt: v{run.prompt_version} | Model: {run.model}")
    print(
        f"Pass rate: {run.pass_rate:.1%} ({sum(c.passed for c in run.case_results)}/{len(run.case_results)})"
    )
    print(
        f"Avg latency: {run.avg_latency_ms:.0f}ms | Tokens: {run.total_tokens:,}"
    )
    print(
        f"Category accuracy: {', '.join(f'{k}={v:.0%}' for k, v in sorted(run.category_accuracy.items()))}"
    )

    if comparison:
        print(f"\n--- Diff vs baseline {comparison.baseline_run_id} ---")
        print(f"Severity: {comparison.severity.value.upper()}")
        delta_pct = comparison.pass_rate_delta * 100
        sign = "+" if delta_pct >= 0 else ""
        print(f"Pass rate delta: {sign}{delta_pct:.1f}%")
        print(
            f"Regressions: {len(comparison.regressions)} | Improvements: {len(comparison.improvements)}"
        )

        if comparison.regressions:
            print("\nRegressed cases:")
            for flip in comparison.regressions[:10]:
                b, c = flip.baseline, flip.current
                print(
                    f"  {flip.case_id}: "
                    f"cat {'✓' if b.category_match else '✗'}→{'✓' if c.category_match else '✗'}, "
                    f"summary {b.summary_score}→{c.summary_score}"
                )
            if len(comparison.regressions) > 10:
                print(f"  ... and {len(comparison.regressions) - 10} more")

    print(f"{'=' * 50}\n")


async def _main(args: argparse.Namespace) -> int:
    config = load_prompt(args.prompt)
    dataset = load_golden_dataset(args.golden)
    thresholds = ThresholdConfig.from_env()

    print(
        f"Running eval: {len(dataset.cases)} cases, concurrency={args.concurrency}"
    )
    if args.skip_judge:
        print("(summary judge skipped — category-only scoring)")

    run = await run_eval(
        config=config,
        dataset=dataset,
        thresholds=thresholds,
        concurrency=args.concurrency,
        skip_judge=args.skip_judge,
    )
    save_run(run)

    comparison = None
    baseline = get_previous_run(run.run_id)
    if baseline:
        expected_categories = _build_expected_categories(dataset)
        comparison = compare_runs(
            baseline, run, expected_categories, thresholds
        )

    _print_summary(run, comparison)

    if args.report_dir:
        report_dir = Path(args.report_dir)
        report_path = generate_html_report(
            run=run,
            output_dir=report_dir,
            comparison=comparison,
            golden_version=args.golden,
        )
        print(f"Report: {report_path}")

        if args.write_pr_comment:
            comment_path = report_dir / "pr_comment.md"
            comment_path.write_text(
                format_pr_comment(run, comparison, report_url=args.report_url)
            )
            print(f"PR comment: {comment_path}")

    if comparison and comparison.severity.value == "critical":
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run golden dataset eval")
    parser.add_argument(
        "--prompt", default="1.0.0", help="Prompt version (e.g. 1.0.0)"
    )
    parser.add_argument(
        "--golden", default="1.0.0", help="Golden dataset version"
    )
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument(
        "--skip-judge",
        action="store_true",
        help="Skip LLM summary judge (faster/cheaper, category-only)",
    )
    parser.add_argument(
        "--report-dir",
        default=None,
        help="Directory to write HTML report (and optional PR comment)",
    )
    parser.add_argument(
        "--write-pr-comment",
        action="store_true",
        help="Write pr_comment.md alongside HTML report",
    )
    parser.add_argument(
        "--report-url",
        default=None,
        help="URL to HTML report for PR comment link",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_main(args)))


if __name__ == "__main__":
    main()
