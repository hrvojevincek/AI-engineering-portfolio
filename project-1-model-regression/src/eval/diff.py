from typing import Dict, List

from src.models import (
    CaseFlip,
    CaseResult,
    EmailCategory,
    EvalRun,
    RunComparison,
    Severity,
    ThresholdConfig,
)


def _case_map(run: EvalRun) -> Dict[str, CaseResult]:
    return {c.case_id: c for c in run.case_results}


def compute_category_accuracy(
    run: EvalRun, expected_categories: Dict[str, str]
) -> Dict[str, float]:
    """Pass rate per expected category (from golden labels)."""
    totals: Dict[str, int] = {c.value: 0 for c in EmailCategory}
    passed: Dict[str, int] = {c.value: 0 for c in EmailCategory}

    for case in run.case_results:
        cat = expected_categories.get(case.case_id, "general")
        totals[cat] = totals.get(cat, 0) + 1
        if case.passed:
            passed[cat] = passed.get(cat, 0) + 1

    return {
        cat: (passed[cat] / totals[cat] if totals[cat] else 0.0)
        for cat in totals
    }


def compare_runs(
    baseline: EvalRun,
    current: EvalRun,
    expected_categories: Dict[str, str],
    thresholds: ThresholdConfig,
) -> RunComparison:
    baseline_map = _case_map(baseline)
    current_map = _case_map(current)

    regressions: List[CaseFlip] = []
    improvements: List[CaseFlip] = []

    for case_id, base_case in baseline_map.items():
        cur_case = current_map.get(case_id)
        if not cur_case:
            continue
        if base_case.passed and not cur_case.passed:
            regressions.append(
                CaseFlip(case_id=case_id, baseline=base_case, current=cur_case)
            )
        elif not base_case.passed and cur_case.passed:
            improvements.append(
                CaseFlip(case_id=case_id, baseline=base_case, current=cur_case)
            )

    pass_rate_delta = current.pass_rate - baseline.pass_rate

    base_cat = compute_category_accuracy(baseline, expected_categories)
    cur_cat = compute_category_accuracy(current, expected_categories)
    category_deltas = {
        cat: cur_cat.get(cat, 0.0) - base_cat.get(cat, 0.0) for cat in base_cat
    }

    severity = _severity(pass_rate_delta, thresholds)

    return RunComparison(
        baseline_run_id=baseline.run_id,
        current_run_id=current.run_id,
        pass_rate_delta=pass_rate_delta,
        category_deltas=category_deltas,
        regressions=regressions,
        improvements=improvements,
        severity=severity,
    )


def _severity(pass_rate_delta: float, thresholds: ThresholdConfig) -> Severity:
    if pass_rate_delta <= -thresholds.critical_delta_pct:
        return Severity.CRITICAL
    if pass_rate_delta <= -thresholds.warn_delta_pct:
        return Severity.WARN
    return Severity.PASS
