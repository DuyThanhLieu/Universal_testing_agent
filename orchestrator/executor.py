from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from adapters.base import BaseAdapter
from orchestrator.models import (
    DefectDetail,
    EvidenceBundle,
    ExecutionEnvelope,
    ExecutionResult,
    NormalizedIntake,
    Recommendation,
    RunMetadata,
    StrategyPlan,
    SummaryStats,
    defect_summary_from_details,
    status_from_summary,
    utc_now_iso,
)


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _duration_seconds(started_at: str, finished_at: str) -> float:
    return round((_parse_iso(finished_at) - _parse_iso(started_at)).total_seconds(), 4)


def _merge_evidence(primary: EvidenceBundle, secondary: EvidenceBundle) -> EvidenceBundle:
    merged = EvidenceBundle(
        logs=[*primary.logs, *secondary.logs],
        screenshots=[*primary.screenshots, *secondary.screenshots],
        traces=[*primary.traces, *secondary.traces],
        artifacts=[*primary.artifacts, *secondary.artifacts],
    )
    # Preserve order while removing duplicates.
    merged.logs = list(dict.fromkeys(merged.logs))
    merged.screenshots = list(dict.fromkeys(merged.screenshots))
    merged.traces = list(dict.fromkeys(merged.traces))
    merged.artifacts = list(dict.fromkeys(merged.artifacts))
    return merged


def _build_recommendation(intake: NormalizedIntake, summary: SummaryStats, defects: list[DefectDetail], notes: list[str]) -> Recommendation:
    counts = defect_summary_from_details(defects)
    min_coverage = float(intake.acceptance.get("coverage_threshold", 0.7))
    coverage_ok = summary.total_checks == 0 or summary.passed / max(summary.total_checks, 1) >= min_coverage
    release_ready = (
        summary.failed == 0
        and summary.blocked == 0
        and counts.blocker == 0
        and counts.critical == 0
        and counts.high == 0
        and coverage_ok
    )
    recommendation_notes = list(notes)
    if not coverage_ok:
        recommendation_notes.append(f"Pass ratio below threshold {min_coverage}.")
    if summary.blocked > 0:
        recommendation_notes.append("Blocked checks detected; investigate unavailable systems or missing inputs.")
    if counts.high > 0 or counts.critical > 0 or counts.blocker > 0:
        recommendation_notes.append("High-severity defects detected; not release-ready.")
    if release_ready and not recommendation_notes:
        recommendation_notes.append("No blocking findings in smoke execution.")
    return Recommendation(release_ready=release_ready, notes=recommendation_notes)


def execute_pipeline(
    intake: NormalizedIntake,
    product_type: str,
    strategy: StrategyPlan,
    adapter: BaseAdapter,
    *,
    run_id: str | None = None,
    started_at: str | None = None,
    run_metadata: RunMetadata | None = None,
) -> ExecutionEnvelope:
    resolved_run_id = run_id or str(uuid4())
    resolved_started_at = started_at or utc_now_iso()
    finished_at = resolved_started_at

    execution = ExecutionResult(
        status="blocked",
        summary=SummaryStats(total_checks=1, passed=0, failed=0, blocked=1, skipped=0),
        recommendation_notes=["Execution was not started."],
    )
    metadata = {
        "manifest_path": intake.manifest_path,
        "acceptance": intake.acceptance,
        "outputs": intake.outputs,
        "strategy": strategy.model_dump(mode="json"),
    }
    known_gaps: list[str] = []
    assumptions: list[str] = []
    generated_artifacts: list[str] = []

    try:
        discovery = adapter.discover(intake)
        adapter_plan = adapter.plan(intake, strategy)
        generated_assets = adapter.generate_assets(intake, adapter_plan)
        generated_artifacts = list(generated_assets.artifacts)
        execution = adapter.execute(intake, generated_assets)
        collected = adapter.collect_evidence(intake, execution)
        execution.evidence = _merge_evidence(execution.evidence, collected)
        metadata["discovery"] = discovery.model_dump(mode="json")
        metadata["adapter_plan"] = adapter_plan.model_dump(mode="json")
        metadata["generated_assets"] = generated_assets.model_dump(mode="json")
        if execution.summary.blocked > 0:
            known_gaps.append("Some execution checks were blocked by unavailable dependencies or targets.")
        assumptions.extend(
            [
                "Smoke execution mode focuses on quick confidence, not exhaustive validation.",
                "Acceptance thresholds are evaluated during reporting policy gate.",
            ]
        )
    except Exception as exc:  # pragma: no cover - defensive fallback
        execution = ExecutionResult(
            status="error",
            summary=SummaryStats(total_checks=1, passed=0, failed=1, blocked=0, skipped=0),
            defect_details=[
                DefectDetail(
                    id="executor.unhandled",
                    severity="critical",
                    message=str(exc),
                    details={"exception_type": type(exc).__name__},
                )
            ],
            evidence=EvidenceBundle(logs=["Execution aborted due to unhandled exception."]),
            recommendation_notes=["Fix executor-level exception before release."],
            raw_output={},
        )

    finished_at = utc_now_iso()
    defects = defect_summary_from_details(execution.defect_details)
    status = "error" if execution.status == "error" else status_from_summary(execution.summary)
    recommendation = _build_recommendation(
        intake=intake,
        summary=execution.summary,
        defects=execution.defect_details,
        notes=execution.recommendation_notes,
    )

    return ExecutionEnvelope(
        run_id=resolved_run_id,
        project_name=intake.name,
        project_type=product_type,
        adapter=adapter.name,
        status=status,
        started_at=resolved_started_at,
        finished_at=finished_at,
        duration_seconds=_duration_seconds(resolved_started_at, finished_at),
        summary=execution.summary,
        coverage=execution.coverage,
        defects=defects,
        defect_details=execution.defect_details,
        evidence=execution.evidence,
        recommendation=recommendation,
        policy=None,
        run_metadata=run_metadata,
        generated_artifacts=generated_artifacts,
        known_gaps=known_gaps,
        assumptions=assumptions,
        metadata=metadata,
        raw_output=execution.raw_output,
    )


def save_execution_result(envelope: ExecutionEnvelope, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(envelope.model_dump(mode="json"), indent=2), encoding="utf-8")
    return path


def load_execution_result(result_path: str | Path) -> ExecutionEnvelope:
    raw = json.loads(Path(result_path).read_text(encoding="utf-8"))
    return ExecutionEnvelope.model_validate(raw)
