from pathlib import Path

from orchestrator.models import (
    CoverageStats,
    DefectDetail,
    DefectSummary,
    EvidenceBundle,
    ExecutionEnvelope,
    Recommendation,
    SummaryStats,
)
from orchestrator.reporter import build_ci_summary, generate_report, save_ci_summary, save_junit_report


def _envelope() -> ExecutionEnvelope:
    return ExecutionEnvelope(
        run_id="run-report-format",
        project_name="format-demo",
        project_type="model",
        adapter="model",
        status="passed",
        started_at="2026-03-20T00:00:00+00:00",
        finished_at="2026-03-20T00:00:01+00:00",
        duration_seconds=1.0,
        summary=SummaryStats(total_checks=4, passed=4, failed=0, blocked=0, skipped=0),
        coverage=CoverageStats(planned_cases=4, executed_cases=4, execution_rate=1.0, requirement_coverage=0.9),
        defects=DefectSummary(),
        defect_details=[
            DefectDetail(
                id="model.example",
                severity="low",
                category="model",
                reproducibility="deterministic",
                confidence_score=0.9,
                message="example",
            )
        ],
        evidence=EvidenceBundle(logs=["ok"], screenshots=[], traces=[], artifacts=[]),
        recommendation=Recommendation(release_ready=True, notes=["ready"]),
        metadata={"acceptance": {"minimum_coverage": 0.5, "max_failed": 0}},
        raw_output={},
    )


def test_junit_report_file_is_generated(tmp_path: Path) -> None:
    report = generate_report(_envelope())
    output = tmp_path / "report.xml"
    save_junit_report(report, output)
    text = output.read_text(encoding="utf-8")
    assert "<testsuite" in text
    assert "quality_gates" in text


def test_ci_summary_file_is_generated(tmp_path: Path) -> None:
    report = generate_report(_envelope())
    output = tmp_path / "ci_summary.json"
    save_ci_summary(report, output)
    payload = build_ci_summary(report)
    assert output.exists()
    assert payload["gate_status"] in {"pass", "warning", "fail"}
