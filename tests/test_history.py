from pathlib import Path

from orchestrator.history import load_history_records, persist_history_record
from orchestrator.models import CoverageStats, DefectSummary, HistoryRecord, SummaryStats


def test_persist_and_load_history_record(tmp_path: Path) -> None:
    history_dir = tmp_path / "history"
    history_index = history_dir / "history_index.json"
    record = HistoryRecord(
        run_id="run-1",
        timestamp="2026-01-01T00:00:00+00:00",
        project_name="demo",
        project_type="api",
        adapter="api",
        status="passed",
        summary=SummaryStats(total_checks=1, passed=1, failed=0, blocked=0, skipped=0),
        coverage=CoverageStats(planned_cases=1, executed_cases=1, execution_rate=1.0, requirement_coverage=1.0),
        defects=DefectSummary(),
        release_ready=True,
    )
    persisted = persist_history_record(record, history_dir, history_index)
    assert persisted.exists()
    assert history_index.exists()

    loaded = load_history_records(history_dir)
    assert len(loaded) == 1
    assert loaded[0].run_id == "run-1"
