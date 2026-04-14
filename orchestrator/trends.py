from __future__ import annotations

import json
from pathlib import Path

from orchestrator.models import HistoryRecord, TrendAnalysis


def _direction(first: float, last: float, *, inverted: bool = False) -> str:
    delta = last - first
    if inverted:
        delta = -delta
    if delta > 0.02:
        return "improving"
    if delta < -0.02:
        return "degrading"
    return "stable"


def analyze_trends(records: list[HistoryRecord]) -> TrendAnalysis:
    if not records:
        return TrendAnalysis(runs_analyzed=0)

    ordered = sorted(records, key=lambda item: item.timestamp)
    pass_rates = [
        item.summary.passed / max(item.summary.total_checks, 1)
        for item in ordered
    ]
    coverages = [item.coverage.requirement_coverage for item in ordered]
    defect_counts = [
        item.defects.blocker + item.defects.critical + item.defects.high + item.defects.medium + item.defects.low
        for item in ordered
    ]
    readiness_rates = [1.0 if item.release_ready else 0.0 for item in ordered]

    pass_rate_trend = _direction(pass_rates[0], pass_rates[-1])
    coverage_trend = _direction(coverages[0], coverages[-1])
    defect_trend = _direction(float(defect_counts[0]), float(defect_counts[-1]), inverted=True)
    release_readiness_trend = _direction(readiness_rates[0], readiness_rates[-1])

    directions = [pass_rate_trend, coverage_trend, defect_trend, release_readiness_trend]
    improving = directions.count("improving")
    degrading = directions.count("degrading")
    if improving > degrading:
        overall = "improving"
    elif degrading > improving:
        overall = "degrading"
    else:
        overall = "stable"

    return TrendAnalysis(
        runs_analyzed=len(ordered),
        overall_direction=overall,
        pass_rate_trend=pass_rate_trend,
        coverage_trend=coverage_trend,
        defect_trend=defect_trend,
        release_readiness_trend=release_readiness_trend,
    )


def render_trends_markdown(trends: TrendAnalysis) -> str:
    return f"""# Run Trends

- Runs analyzed: `{trends.runs_analyzed}`
- Overall direction: `{trends.overall_direction}`
- Pass rate trend: `{trends.pass_rate_trend}`
- Coverage trend: `{trends.coverage_trend}`
- Defect trend: `{trends.defect_trend}`
- Release readiness trend: `{trends.release_readiness_trend}`
"""


def save_trends(trends: TrendAnalysis, output_json: str | Path, output_md: str | Path) -> tuple[Path, Path]:
    json_path = Path(output_json)
    md_path = Path(output_md)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(trends.model_dump(mode="json"), indent=2), encoding="utf-8")
    md_path.write_text(render_trends_markdown(trends), encoding="utf-8")
    return json_path, md_path


def flaky_suspicion_from_history(records: list[HistoryRecord]) -> str | None:
    if len(records) < 4:
        return None
    ordered = sorted(records, key=lambda item: item.timestamp)
    statuses = [item.status for item in ordered[-6:]]
    switches = sum(1 for i in range(1, len(statuses)) if statuses[i] != statuses[i - 1])
    if switches >= 3:
        return "Potential flaky behavior detected: recent run outcomes are frequently switching."
    return None
