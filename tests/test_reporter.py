from orchestrator.models import (
    CoverageStats,
    DefectSummary,
    EvidenceBundle,
    ExecutionEnvelope,
    PolicyEvaluation,
    Recommendation,
    RunMetadata,
    SummaryStats,
)
from orchestrator.reporter import generate_report, render_markdown_report


def test_reporter_contains_required_contract_fields() -> None:
    envelope = ExecutionEnvelope(
        run_id="run-1",
        project_name="web-booking-demo",
        project_type="web",
        adapter="web",
        status="passed",
        started_at="2026-01-01T00:00:00Z",
        finished_at="2026-01-01T00:00:01Z",
        duration_seconds=1.0,
        summary=SummaryStats(total_checks=2, passed=2, failed=0, blocked=0, skipped=0),
        coverage=CoverageStats(planned_cases=2, executed_cases=2, execution_rate=1.0, requirement_coverage=1.0),
        defects=DefectSummary(),
        evidence=EvidenceBundle(logs=["ok"], screenshots=[], traces=[], artifacts=[]),
        recommendation=Recommendation(release_ready=True, notes=["ready"]),
        policy=PolicyEvaluation(release_ready=True, verdict="pass", reasons=[], evaluated_rules={}),
        run_metadata=RunMetadata(
            run_id="run-1",
            command="run",
            project_name="web-booking-demo",
            project_type="web",
            manifest_path="manifests/samples/web_booking.yaml",
            started_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:00:01Z",
            duration_seconds=1.0,
            status="passed",
            artifact_dir="results/runs/run-1",
        ),
        generated_artifacts=[],
        known_gaps=[],
        assumptions=[],
        metadata={},
        raw_output={},
    )

    report = generate_report(envelope)
    assert report.summary.total_checks == 2
    assert report.defects.high == 0
    assert report.policy.verdict in {"pass", "fail"}
    assert report.release_gate_summary in {"PASS", "FAIL"}


def test_markdown_report_renders_sections() -> None:
    envelope = ExecutionEnvelope(
        run_id="run-2",
        project_name="api-demo",
        project_type="api",
        adapter="api",
        status="blocked",
        started_at="2026-01-01T00:00:00Z",
        finished_at="2026-01-01T00:00:02Z",
        duration_seconds=2.0,
        summary=SummaryStats(total_checks=1, passed=0, failed=0, blocked=1, skipped=0),
        coverage=CoverageStats(planned_cases=1, executed_cases=1, execution_rate=1.0, requirement_coverage=0.5),
        defects=DefectSummary(),
        evidence=EvidenceBundle(logs=["blocked"], screenshots=[], traces=[], artifacts=[]),
        recommendation=Recommendation(release_ready=False, notes=["blocked"]),
        policy=PolicyEvaluation(release_ready=False, verdict="fail", reasons=["x"], evaluated_rules={}),
        run_metadata=None,
        generated_artifacts=[],
        known_gaps=[],
        assumptions=[],
        metadata={},
        raw_output={},
    )
    markdown = render_markdown_report(generate_report(envelope))
    assert "## Project Summary" in markdown
    assert "## Execution Summary" in markdown
    assert "## Release Recommendation" in markdown
    assert "## Policy Evaluation" in markdown
    assert "## Quality Gates" in markdown
    assert "## Capabilities Used" in markdown
    assert "## Capability Coverage Summary" in markdown
    assert "## Taxonomy Coverage Focus" in markdown
    assert "## Fallback Execution Note" in markdown
    assert "## Plugin Onboarding" in markdown
    assert "## Support Level" in markdown
    assert "## Coverage Catalog Reference" in markdown
    assert "## Trend Summary" in markdown
    assert "## Contract Validation Summary" in markdown
    assert "## Comparison Summary" in markdown


def test_reporter_includes_plugin_metadata_from_envelope() -> None:
    envelope = ExecutionEnvelope(
        run_id="run-3",
        project_name="llm-demo",
        project_type="llm_app",
        adapter="llm_app",
        status="passed",
        started_at="2026-01-01T00:00:00Z",
        finished_at="2026-01-01T00:00:03Z",
        duration_seconds=3.0,
        summary=SummaryStats(total_checks=3, passed=3, failed=0, blocked=0, skipped=0),
        coverage=CoverageStats(planned_cases=3, executed_cases=3, execution_rate=1.0, requirement_coverage=1.0),
        defects=DefectSummary(),
        evidence=EvidenceBundle(logs=["ok"], screenshots=[], traces=[], artifacts=[]),
        recommendation=Recommendation(release_ready=True, notes=["ready"]),
        plugin={
            "plugin_name": "llm_app",
            "plugin_version": "1.8.0",
            "author": "UTA Core Team",
            "dependencies": ["requests>=2.31"],
            "compatibility": {"python": ">=3.11,<3.13"},
            "supported_product_types": ["llm_app"],
            "supported_capabilities": ["reporting"],
            "fallback_mode": "skeleton_smoke",
            "adapter_target": "LlmAppAdapter",
            "health_metadata": {"origin": "builtin"},
            "discovered_from": "builtin",
        },
        plugin_validation={
            "valid": True,
            "errors": [],
            "warnings": [],
            "adapter_method_coverage": ["discover", "plan", "generate_assets", "execute", "collect_evidence"],
            "capability_completeness": 1.0,
            "missing_recommended_capabilities": [],
            "support_level": "fallback_only",
            "fallback_support_note": "skeleton",
        },
        plugin_onboarding={
            "plugin_name": "llm_app",
            "onboarding_status": "ready",
            "completeness_score": 1.0,
            "missing_items": [],
            "notes": ["ok"],
        },
        support_level="fallback_only",
        capability_path_used=["discovery", "reporting"],
        policy=None,
        run_metadata=None,
        generated_artifacts=[],
        known_gaps=[],
        assumptions=[],
        metadata={"coverage_catalog_reference": "results/coverage_catalog_latest.json"},
        raw_output={},
    )
    report = generate_report(envelope)
    assert report.plugin is not None
    assert report.plugin.plugin_name == "llm_app"
    assert report.plugin_validation is not None
    assert report.plugin_onboarding is not None
    assert report.support_level == "fallback_only"
    assert report.capability_path_used == ["discovery", "reporting"]
