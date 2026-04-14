import json
from pathlib import Path

from orchestrator.compare import compare_results


def _result_payload(*, passed: int, failed: int, coverage: float, defects_high: int, release_ready: bool) -> dict:
    return {
        "run_id": "run-test",
        "project_name": "demo",
        "project_type": "api",
        "adapter": "api",
        "status": "passed" if failed == 0 else "failed",
        "started_at": "2026-01-01T00:00:00+00:00",
        "finished_at": "2026-01-01T00:00:01+00:00",
        "duration_seconds": 1.0,
        "summary": {"total_checks": passed + failed, "passed": passed, "failed": failed, "blocked": 0, "skipped": 0},
        "coverage": {"planned_cases": 5, "executed_cases": 5, "execution_rate": 1.0, "requirement_coverage": coverage},
        "defects": {"blocker": 0, "critical": 0, "high": defects_high, "medium": 0, "low": 0},
        "evidence": {"logs": [], "screenshots": [], "traces": [], "artifacts": []},
        "recommendation": {"release_ready": release_ready, "notes": []},
        "policy": None,
        "run_metadata": None,
        "generated_artifacts": [],
        "known_gaps": [],
        "assumptions": [],
        "metadata": {},
        "raw_output": {},
    }


def test_compare_results_detects_regression(tmp_path: Path) -> None:
    current_file = tmp_path / "current.json"
    baseline_file = tmp_path / "baseline.json"
    current_file.write_text(
        json.dumps(_result_payload(passed=2, failed=2, coverage=0.4, defects_high=2, release_ready=False)),
        encoding="utf-8",
    )
    baseline_file.write_text(
        json.dumps(_result_payload(passed=4, failed=0, coverage=0.8, defects_high=0, release_ready=True)),
        encoding="utf-8",
    )
    comparison = compare_results(current_file, baseline_file)
    assert comparison.changed is True
    assert comparison.failed_delta > 0
    assert comparison.regression_signals
