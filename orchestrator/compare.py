from __future__ import annotations

import json
from pathlib import Path

from orchestrator.executor import load_execution_result
from orchestrator.models import ComparisonResult


def _defect_total(payload: dict[str, int]) -> int:
    return sum(payload.get(key, 0) for key in ("blocker", "critical", "high", "medium", "low"))


def compare_results(current_result_path: str | Path, baseline_result_path: str | Path) -> ComparisonResult:
    current = load_execution_result(current_result_path)
    baseline = load_execution_result(baseline_result_path)

    passed_delta = current.summary.passed - baseline.summary.passed
    failed_delta = current.summary.failed - baseline.summary.failed
    coverage_delta = round(current.coverage.requirement_coverage - baseline.coverage.requirement_coverage, 4)
    current_defects = _defect_total(current.defects.model_dump(mode="json"))
    baseline_defects = _defect_total(baseline.defects.model_dump(mode="json"))
    defect_delta = current_defects - baseline_defects
    release_ready_changed = current.recommendation.release_ready != baseline.recommendation.release_ready

    regression_signals: list[str] = []
    if passed_delta < 0:
        regression_signals.append("Passed checks decreased compared to baseline.")
    if failed_delta > 0:
        regression_signals.append("Failed checks increased compared to baseline.")
    if coverage_delta < 0:
        regression_signals.append("Requirement coverage decreased compared to baseline.")
    if defect_delta > 0:
        regression_signals.append("Total defect count increased compared to baseline.")
    if release_ready_changed and not current.recommendation.release_ready:
        regression_signals.append("Release readiness regressed to not-ready.")

    changed = any([passed_delta != 0, failed_delta != 0, coverage_delta != 0, defect_delta != 0, release_ready_changed])
    return ComparisonResult(
        current_result_path=str(current_result_path),
        baseline_result_path=str(baseline_result_path),
        changed=changed,
        passed_delta=passed_delta,
        failed_delta=failed_delta,
        coverage_delta=coverage_delta,
        defect_delta=defect_delta,
        release_ready_changed=release_ready_changed,
        regression_signals=regression_signals,
    )


def render_comparison_markdown(result: ComparisonResult) -> str:
    lines = [
        "# Result Comparison",
        "",
        f"- Current: `{result.current_result_path}`",
        f"- Baseline: `{result.baseline_result_path}`",
        f"- Changed: `{result.changed}`",
        f"- Passed delta: `{result.passed_delta}`",
        f"- Failed delta: `{result.failed_delta}`",
        f"- Coverage delta: `{result.coverage_delta}`",
        f"- Defect delta: `{result.defect_delta}`",
        f"- Release ready changed: `{result.release_ready_changed}`",
        "",
        "## Regression Signals",
    ]
    if result.regression_signals:
        lines.extend([f"- {item}" for item in result.regression_signals])
    else:
        lines.append("- (none)")
    lines.append("")
    return "\n".join(lines)


def save_comparison(result: ComparisonResult, output_json: str | Path, output_md: str | Path) -> tuple[Path, Path]:
    json_path = Path(output_json)
    md_path = Path(output_md)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result.model_dump(mode="json"), indent=2), encoding="utf-8")
    md_path.write_text(render_comparison_markdown(result), encoding="utf-8")
    return json_path, md_path
