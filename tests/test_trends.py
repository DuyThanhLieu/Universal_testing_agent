from orchestrator.models import CoverageStats, DefectSummary, HistoryRecord, SummaryStats
from orchestrator.trends import analyze_trends


def _record(run_id: str, passed: int, failed: int, coverage: float, defects: int, ready: bool, ts: str) -> HistoryRecord:
    return HistoryRecord(
        run_id=run_id,
        timestamp=ts,
        project_name="demo",
        project_type="api",
        adapter="api",
        status="passed" if failed == 0 else "failed",
        summary=SummaryStats(total_checks=5, passed=passed, failed=failed, blocked=0, skipped=0),
        coverage=CoverageStats(planned_cases=5, executed_cases=5, execution_rate=1.0, requirement_coverage=coverage),
        defects=DefectSummary(high=defects),
        release_ready=ready,
    )


def test_analyze_trends_detects_improving_direction() -> None:
    trends = analyze_trends(
        [
            _record("r1", 2, 3, 0.4, 4, False, "2026-01-01T00:00:00+00:00"),
            _record("r2", 3, 2, 0.5, 3, False, "2026-01-02T00:00:00+00:00"),
            _record("r3", 4, 1, 0.7, 1, True, "2026-01-03T00:00:00+00:00"),
        ]
    )
    assert trends.runs_analyzed == 3
    assert trends.overall_direction in {"improving", "stable", "degrading"}
    assert trends.pass_rate_trend == "improving"
