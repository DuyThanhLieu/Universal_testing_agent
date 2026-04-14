from __future__ import annotations

import json
from pathlib import Path

from orchestrator.models import ExecutionEnvelope, HistoryRecord, StandardReport, utc_now_iso


def _record_filename(record: HistoryRecord) -> str:
    timestamp = record.timestamp.replace(":", "-")
    return f"{timestamp}_{record.run_id}.json"


def record_from_execution(envelope: ExecutionEnvelope) -> HistoryRecord:
    return HistoryRecord(
        run_id=envelope.run_id,
        timestamp=utc_now_iso(),
        project_name=envelope.project_name,
        project_type=envelope.project_type,
        adapter=envelope.adapter,
        status=envelope.status,
        summary=envelope.summary,
        coverage=envelope.coverage,
        defects=envelope.defects,
        release_ready=envelope.recommendation.release_ready,
    )


def record_from_report(report: StandardReport) -> HistoryRecord:
    return HistoryRecord(
        run_id=report.run_id,
        timestamp=utc_now_iso(),
        project_name=report.project_name,
        project_type=report.project_type,
        adapter=report.adapter,
        status=report.status,
        summary=report.summary,
        coverage=report.coverage,
        defects=report.defects,
        release_ready=report.recommendation.release_ready,
    )


def persist_history_record(record: HistoryRecord, history_dir: str | Path, history_index_file: str | Path) -> Path:
    history_dir_path = Path(history_dir)
    history_dir_path.mkdir(parents=True, exist_ok=True)
    index_path = Path(history_index_file)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    record_path = history_dir_path / _record_filename(record)
    record_path.write_text(json.dumps(record.model_dump(mode="json"), indent=2), encoding="utf-8")

    if index_path.exists():
        try:
            index_data = json.loads(index_path.read_text(encoding="utf-8"))
        except Exception:
            index_data = {"records": []}
    else:
        index_data = {"records": []}

    records = index_data.get("records", [])
    records = [item for item in records if item.get("run_id") != record.run_id or item.get("path") != str(record_path)]
    records.append(
        {
            "run_id": record.run_id,
            "timestamp": record.timestamp,
            "project_name": record.project_name,
            "project_type": record.project_type,
            "status": record.status,
            "release_ready": record.release_ready,
            "path": str(record_path),
        }
    )
    index_data["records"] = sorted(records, key=lambda item: item.get("timestamp", ""))
    index_path.write_text(json.dumps(index_data, indent=2), encoding="utf-8")
    return record_path


def load_history_records(history_dir: str | Path) -> list[HistoryRecord]:
    directory = Path(history_dir)
    if not directory.exists():
        return []
    records: list[HistoryRecord] = []
    for file_path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            records.append(HistoryRecord.model_validate(payload))
        except Exception:
            continue
    return records
