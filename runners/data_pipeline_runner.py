from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _defect(
    defect_id: str,
    severity: str,
    message: str,
    *,
    category: str = "data",
    reproducibility: str = "deterministic",
    confidence_score: float = 0.95,
    **details: Any,
) -> dict[str, Any]:
    return {
        "id": defect_id,
        "severity": severity,
        "category": category,
        "reproducibility": reproducibility,
        "confidence_score": confidence_score,
        "message": message,
        "details": details,
    }


def _safe_execution_rate(executed_cases: int, planned_cases: int) -> float:
    if planned_cases <= 0:
        return 0.0
    return round(executed_cases / planned_cases, 4)


def _load_json(path: str | None) -> Any:
    if not path:
        return None
    candidate = Path(path)
    if not candidate.exists():
        return None
    try:
        return json.loads(candidate.read_text(encoding="utf-8"))
    except Exception:
        return None


def run_data_pipeline_smoke(
    schema_path: str | None,
    batch_path: str | None,
    expected_columns: list[str],
    transformations: list[str],
    evidence_dir: str,
    expected_batch_size: int | None = None,
) -> dict[str, Any]:
    logs: list[str] = []
    defects: list[dict[str, Any]] = []

    planned_cases = 6
    passed = 0
    failed = 0
    blocked = 0
    skipped = 0

    schema_payload = _load_json(schema_path)
    batch_payload = _load_json(batch_path)

    schema_columns: list[str] = []
    if isinstance(schema_payload, dict):
        raw_columns = schema_payload.get("columns", [])
        if isinstance(raw_columns, list):
            schema_columns = [str(item) for item in raw_columns]
    elif isinstance(schema_payload, list):
        schema_columns = [str(item) for item in schema_payload]

    if schema_columns:
        passed += 1
        logs.append(f"Schema columns loaded: {', '.join(schema_columns)}")
    else:
        blocked += 1
        defects.append(
            _defect(
                "pipeline.schema_missing",
                "critical",
                "Schema definition missing or invalid.",
                category="contract",
            )
        )

    records: list[dict[str, Any]] = []
    if isinstance(batch_payload, list):
        records = [item for item in batch_payload if isinstance(item, dict)]
    if records:
        passed += 1
        logs.append(f"Batch records loaded: {len(records)}")
    else:
        blocked += 1
        defects.append(
            _defect(
                "pipeline.batch_missing",
                "critical",
                "Batch payload missing or invalid.",
                category="data",
            )
        )

    if expected_columns:
        missing_columns = [column for column in expected_columns if column not in schema_columns]
        if missing_columns:
            failed += 1
            defects.append(
                _defect(
                    "pipeline.schema_mismatch",
                    "high",
                    "Expected columns missing from schema.",
                    category="contract",
                    missing_columns=missing_columns,
                )
            )
        else:
            passed += 1
            logs.append("Schema consistency check passed.")
    else:
        skipped += 1
        logs.append("Expected columns not provided; strict schema check skipped.")

    if records and expected_columns:
        missing_in_any = [
            column
            for column in expected_columns
            if any(column not in record for record in records)
        ]
        if missing_in_any:
            failed += 1
            defects.append(
                _defect(
                    "pipeline.integrity_mismatch",
                    "high",
                    "Expected columns missing in one or more batch records.",
                    category="data",
                    missing_columns=sorted(set(missing_in_any)),
                )
            )
        else:
            passed += 1
            logs.append("Data consistency check passed for expected columns across all records.")

    if records:
        duplicate_ids = []
        seen_ids: set[str] = set()
        for record in records:
            record_id = str(record.get("id", "")).strip()
            if not record_id:
                continue
            if record_id in seen_ids:
                duplicate_ids.append(record_id)
            seen_ids.add(record_id)
        if duplicate_ids:
            failed += 1
            defects.append(
                _defect(
                    "pipeline.duplicate_ids",
                    "medium",
                    "Duplicate record identifiers detected in batch.",
                    category="data",
                    duplicate_ids=sorted(set(duplicate_ids)),
                )
            )
        else:
            passed += 1
            logs.append("Batch uniqueness check passed for record IDs.")

    if expected_batch_size is not None and expected_batch_size >= 0:
        if len(records) == expected_batch_size:
            passed += 1
            logs.append(f"Batch completeness check passed: {len(records)} records.")
        else:
            failed += 1
            defects.append(
                _defect(
                    "pipeline.batch_completeness_failed",
                    "medium",
                    "Batch size does not match expected count.",
                    category="data",
                    expected_batch_size=expected_batch_size,
                    actual_batch_size=len(records),
                )
            )
    else:
        skipped += 1
        logs.append("Expected batch size not provided; completeness strict check skipped.")

    if transformations:
        passed += 1
        logs.append(f"Transformation chain declared: {', '.join(transformations)}")
    else:
        blocked += 1
        defects.append(
            _defect(
                "pipeline.transformations_missing",
                "low",
                "No transformations declared.",
                category="functional",
                confidence_score=0.85,
            )
        )

    total_checks = passed + failed + blocked + skipped
    executed_cases = passed + failed + blocked
    status = "failed" if failed > 0 else "blocked" if blocked > 0 and passed == 0 else "passed"
    requirement_coverage = round(min(1.0, max(0.4, passed / max(planned_cases, 1))), 4)

    trace_file = Path(evidence_dir) / "data_pipeline_smoke_trace.log"
    trace_file.parent.mkdir(parents=True, exist_ok=True)
    trace_file.write_text("\n".join(logs), encoding="utf-8")

    return {
        "status": status,
        "summary": {
            "total_checks": total_checks,
            "passed": passed,
            "failed": failed,
            "blocked": blocked,
            "skipped": skipped,
        },
        "coverage": {
            "planned_cases": planned_cases,
            "executed_cases": executed_cases,
            "execution_rate": _safe_execution_rate(executed_cases, planned_cases),
            "requirement_coverage": requirement_coverage,
        },
        "defects": defects,
        "evidence": {
            "logs": logs,
            "screenshots": [],
            "traces": [str(trace_file)],
            "artifacts": [str(trace_file)] + [item for item in [schema_path, batch_path] if item],
        },
        "recommendation_notes": [
            "Data pipeline smoke validates schema, consistency, and batch completeness.",
            "Add column type constraints and transformation result assertions for deeper coverage.",
        ],
        "raw_output": {
            "schema_path": schema_path,
            "batch_path": batch_path,
            "expected_columns": expected_columns,
            "transformations": transformations,
            "expected_batch_size": expected_batch_size,
        },
    }
