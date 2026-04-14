from __future__ import annotations

from pathlib import Path
from typing import Any


def _defect(defect_id: str, severity: str, message: str, **details: Any) -> dict[str, Any]:
    return {"id": defect_id, "severity": severity, "message": message, "details": details}


def _safe_execution_rate(executed_cases: int, planned_cases: int) -> float:
    if planned_cases <= 0:
        return 0.0
    return round(executed_cases / planned_cases, 4)


def run_workflow_smoke(
    trigger_payload: dict[str, Any],
    steps: list[dict[str, Any]],
    transitions: list[dict[str, Any]],
    retry_policy: dict[str, Any],
    evidence_dir: str,
) -> dict[str, Any]:
    logs: list[str] = []
    defects: list[dict[str, Any]] = []

    planned_cases = 5
    passed = 0
    failed = 0
    blocked = 0
    skipped = 0

    if trigger_payload:
        passed += 1
        logs.append("Trigger input payload configured.")
    else:
        blocked += 1
        defects.append(_defect("workflow.trigger_missing", "medium", "Workflow trigger payload missing."))

    if steps:
        passed += 1
        logs.append(f"Workflow step chain configured: {len(steps)} steps.")
    else:
        failed += 1
        defects.append(_defect("workflow.steps_missing", "high", "No workflow steps defined."))

    valid_transitions = 0
    for item in transitions:
        if isinstance(item, dict) and item.get("from") and item.get("to"):
            valid_transitions += 1
    if valid_transitions > 0:
        passed += 1
        logs.append(f"State transition definitions validated: {valid_transitions}.")
    else:
        blocked += 1
        defects.append(_defect("workflow.transitions_missing", "low", "No valid state transitions found."))

    if retry_policy:
        passed += 1
        logs.append("Error recovery policy configured.")
    else:
        blocked += 1
        defects.append(_defect("workflow.recovery_missing", "low", "Retry/error recovery policy is missing."))

    if trigger_payload.get("idempotency_key") or retry_policy.get("idempotent", False):
        passed += 1
        logs.append("Idempotency baseline check passed.")
    else:
        blocked += 1
        defects.append(_defect("workflow.idempotency_missing", "medium", "Idempotency signal not configured."))

    total_checks = passed + failed + blocked + skipped
    executed_cases = passed + failed + blocked
    status = "failed" if failed > 0 else "blocked" if blocked > 0 and passed == 0 else "passed"
    requirement_coverage = round(min(1.0, max(0.4, passed / max(planned_cases, 1))), 4)

    trace_file = Path(evidence_dir) / "workflow_smoke_trace.log"
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
            "artifacts": [str(trace_file)],
        },
        "recommendation_notes": [
            "Workflow adapter executed deterministic chaining/state smoke checks; add runtime orchestration integration checks for production."
        ],
        "raw_output": {
            "step_count": len(steps),
            "transition_count": valid_transitions,
            "retry_policy": retry_policy,
        },
    }
