"""Generate HTML eval diff reports."""

from pathlib import Path
from typing import Dict, Optional

from src.eval.dataset import load_golden_dataset
from src.eval.store import get_recent_run_summaries
from src.models import EvalRun, RunComparison

REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Eval Report — {{ run.run_id }}</title>
  <style>
    :root { --bg: #0f1117; --card: #1a1d27; --text: #e6e6e6; --muted: #8b8fa3;
            --pass: #3dd68c; --warn: #f5a623; --crit: #ff5c5c; --border: #2a2e3d; }
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--text);
           margin: 0; padding: 2rem; line-height: 1.5; }
    h1, h2 { margin: 0 0 1rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }
    .label { color: var(--muted); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.04em; }
    .value { font-size: 1.5rem; font-weight: 600; margin-top: 0.25rem; }
    .severity-pass { color: var(--pass); }
    .severity-warn { color: var(--warn); }
    .severity-critical { color: var(--crit); }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.9rem; }
    th, td { border: 1px solid var(--border); padding: 0.6rem 0.75rem; text-align: left; vertical-align: top; }
    th { background: var(--card); color: var(--muted); }
    .email { color: var(--muted); font-size: 0.85rem; max-width: 280px; white-space: pre-wrap; }
    .chart { display: flex; align-items: flex-end; gap: 6px; height: 120px; margin-top: 1rem; }
    .bar { flex: 1; background: #3b82f6; border-radius: 4px 4px 0 0; min-width: 12px; position: relative; }
    .bar span { position: absolute; bottom: -1.4rem; left: 50%; transform: translateX(-50%);
                 font-size: 0.65rem; color: var(--muted); white-space: nowrap; }
    .section { margin-top: 2rem; }
    .mono { font-family: ui-monospace, monospace; font-size: 0.85rem; }
  </style>
</head>
<body>
  <h1>Model Eval Report</h1>
  <p class="mono">{{ run.timestamp }} · prompt v{{ run.prompt_version }} · {{ run.model }}</p>

  <div class="grid section">
    <div class="card">
      <div class="label">Pass rate</div>
      <div class="value">{{ "%.1f"|format(run.pass_rate * 100) }}%</div>
      <div class="label">{{ passed_count }}/{{ total_count }} cases</div>
    </div>
    <div class="card">
      <div class="label">Avg latency</div>
      <div class="value">{{ "%.0f"|format(run.avg_latency_ms) }}ms</div>
    </div>
    <div class="card">
      <div class="label">Tokens used</div>
      <div class="value">{{ "{:,}".format(run.total_tokens) }}</div>
    </div>
    {% if comparison %}
    <div class="card">
      <div class="label">Severity</div>
      <div class="value severity-{{ comparison.severity.value }}">{{ comparison.severity.value | upper }}</div>
      <div class="label">Δ pass rate {{ "%+.1f"|format(comparison.pass_rate_delta * 100) }}%</div>
    </div>
    {% endif %}
  </div>

  {% if comparison %}
  <div class="section">
    <h2>Scorecard vs baseline</h2>
    <div class="grid">
      <div class="card">
        <div class="label">Baseline run</div>
        <div class="mono">{{ comparison.baseline_run_id }}</div>
      </div>
      <div class="card">
        <div class="label">Regressions</div>
        <div class="value severity-critical">{{ comparison.regressions | length }}</div>
      </div>
      <div class="card">
        <div class="label">Improvements</div>
        <div class="value severity-pass">{{ comparison.improvements | length }}</div>
      </div>
    </div>
    <table>
      <tr><th>Category</th><th>Baseline</th><th>Current</th><th>Delta</th></tr>
      {% for cat, delta in comparison.category_deltas.items() %}
      <tr>
        <td>{{ cat }}</td>
        <td>{{ "%.0f"|format((baseline_category.get(cat, 0)) * 100) }}%</td>
        <td>{{ "%.0f"|format((run.category_accuracy.get(cat, 0)) * 100) }}%</td>
        <td class="{% if delta < 0 %}severity-critical{% elif delta > 0 %}severity-pass{% endif %}">
          {{ "%+.0f"|format(delta * 100) }}%
        </td>
      </tr>
      {% endfor %}
    </table>
  </div>
  {% endif %}

  {% if history %}
  <div class="section">
    <h2>Pass rate trend (last {{ history | length }} runs)</h2>
    <div class="chart">
      {% for h in history %}
      <div class="bar" style="height: {{ (h.pass_rate * 100) | int }}%"
           title="v{{ h.prompt_version }} — {{ "%.0f"|format(h.pass_rate * 100) }}%">
        <span>{{ "%.0f"|format(h.pass_rate * 100) }}%</span>
      </div>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  {% if comparison and comparison.regressions %}
  <div class="section">
    <h2>Regressions ({{ comparison.regressions | length }})</h2>
    <table>
      <tr>
        <th>Case</th><th>Email</th>
        <th>Baseline</th><th>Current</th>
      </tr>
      {% for flip in comparison.regressions %}
      <tr>
        <td class="mono">{{ flip.case_id }}</td>
        <td class="email">{{ case_inputs.get(flip.case_id, "") }}</td>
        <td>
          {{ flip.baseline.actual.category.value }} · score {{ flip.baseline.summary_score }}
          {% if flip.baseline.passed %}✓{% else %}✗{% endif %}<br>
          <span class="email">{{ flip.baseline.actual.summary }}</span>
        </td>
        <td>
          {{ flip.current.actual.category.value }} · score {{ flip.current.summary_score }}
          {% if flip.current.passed %}✓{% else %}✗{% endif %}<br>
          <span class="email">{{ flip.current.actual.summary }}</span>
        </td>
      </tr>
      {% endfor %}
    </table>
  </div>
  {% endif %}
</body>
</html>"""


def _baseline_category_accuracy(
    comparison: RunComparison, run: EvalRun
) -> Dict[str, float]:
    baseline: Dict[str, float] = {}
    for cat in run.category_accuracy:
        baseline[cat] = run.category_accuracy[
            cat
        ] - comparison.category_deltas.get(cat, 0.0)
    return baseline


def generate_html_report(
    run: EvalRun,
    output_dir: Path,
    comparison: Optional[RunComparison] = None,
    golden_version: str = "1.0.0",
    history_limit: int = 10,
) -> Path:
    from jinja2 import Template

    output_dir.mkdir(parents=True, exist_ok=True)
    dataset = load_golden_dataset(golden_version)
    case_inputs = {c.id: c.input for c in dataset.cases}
    history = get_recent_run_summaries(history_limit)

    baseline_category: Dict[str, float] = {}
    if comparison:
        baseline_category = _baseline_category_accuracy(comparison, run)

    html = Template(REPORT_TEMPLATE).render(
        run=run,
        comparison=comparison,
        passed_count=sum(c.passed for c in run.case_results),
        total_count=len(run.case_results),
        case_inputs=case_inputs,
        history=history,
        baseline_category=baseline_category,
    )

    report_path = output_dir / f"{run.run_id}.html"
    report_path.write_text(html)
    return report_path
