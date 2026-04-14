from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _defect(defect_id: str, severity: str, message: str, **details: Any) -> dict[str, Any]:
    return {"id": defect_id, "severity": severity, "message": message, "details": details}


def _safe_execution_rate(executed_cases: int, planned_cases: int) -> float:
    if planned_cases <= 0:
        return 0.0
    return round(executed_cases / planned_cases, 4)


def _dataset_samples(dataset_path: str | None) -> list[dict[str, Any]]:
    if not dataset_path:
        return []
    path = Path(dataset_path)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def run_llm_app_smoke(
    eval_cases: list[dict[str, Any]],
    labels: list[str],
    dataset_path: str | None,
    tool_names: list[str],
    fallback_strategy: str,
    evidence_dir: str,
) -> dict[str, Any]:
    logs: list[str] = []
    defects: list[dict[str, Any]] = []
    dataset_samples = _dataset_samples(dataset_path)

    planned_cases = max(len(eval_cases), 1) + 4
    passed = 0
    failed = 0
    blocked = 0
    skipped = 0

    if labels:
        passed += 1
        logs.append(f"Label taxonomy loaded: {len(labels)}")
    else:
        blocked += 1
        defects.append(_defect("llm.labels_missing", "low", "No label taxonomy configured for llm_app evaluation."))

    if dataset_samples:
        passed += 1
        logs.append(f"Dataset samples loaded: {len(dataset_samples)}")
    else:
        blocked += 1
        defects.append(_defect("llm.dataset_missing", "low", "No llm_app dataset samples available."))

    if tool_names:
        passed += 1
        logs.append(f"Tool readiness checks prepared: {', '.join(tool_names)}")
    else:
        blocked += 1
        defects.append(_defect("llm.tools_missing", "low", "No tools declared for tool-use readiness checks."))

    if fallback_strategy:
        passed += 1
        logs.append(f"Fallback strategy configured: {fallback_strategy}")
    else:
        blocked += 1
        defects.append(_defect("llm.fallback_missing", "medium", "No fallback strategy configured."))

    for index, case in enumerate(eval_cases or [{"prompt": "health check", "expected_contains": "ok"}], start=1):
        prompt = str(case.get("prompt", ""))
        expected = str(case.get("expected_contains", "")).lower().strip()
        candidate = str(case.get("mock_response", prompt)).lower()
        if expected and expected in candidate:
            passed += 1
            logs.append(f"Case {index}: expected token detected.")
        elif expected:
            failed += 1
            defects.append(
                _defect(
                    "llm.expected_token_missing",
                    "medium",
                    "Expected token not present in simulated response.",
                    case_index=index,
                    expected_contains=expected,
                )
            )
        else:
            skipped += 1
            logs.append(f"Case {index}: no explicit expected token; skipped strict assertion.")

    total_checks = passed + failed + blocked + skipped
    executed_cases = passed + failed + blocked
    status = "failed" if failed > 0 else "blocked" if blocked > 0 and passed == 0 else "passed"
    requirement_coverage = round(min(1.0, max(0.4, passed / max(planned_cases, 1))), 4)

    trace_file = Path(evidence_dir) / "llm_app_smoke_trace.log"
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
            "artifacts": [str(trace_file)] + ([dataset_path] if dataset_path else []),
        },
        "recommendation_notes": [
            "llm_app adapter ran deterministic skeleton checks; add live judge/evaluator integrations for deeper validation."
        ],
        "raw_output": {
            "skeleton_mode": True,
            "tool_names": tool_names,
            "fallback_strategy": fallback_strategy,
            "dataset_path": dataset_path,
        },
    }
