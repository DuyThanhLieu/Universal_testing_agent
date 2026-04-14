from __future__ import annotations

from adapters.base import BaseAdapter
from orchestrator.models import (
    AdapterPlan,
    DiscoveryResult,
    EvidenceBundle,
    ExecutionResult,
    GeneratedAssets,
    NormalizedIntake,
    StrategyPlan,
)
from runners.mobile_runner import run_mobile_smoke


class MobileAdapter(BaseAdapter):
    name = "mobile"

    def discover(self, intake: NormalizedIntake) -> DiscoveryResult:
        app_id = str(intake.request.get("app_id") or intake.environment.get("app_id") or "").strip()
        artifact_paths = [artifact.path for artifact in intake.artifacts if artifact.path]
        entry_points = intake.entry_points or intake.request.get("entry_points", [])
        return DiscoveryResult(
            items=[app_id, *artifact_paths],
            metadata={"adapter": self.name, "entry_points": entry_points},
        )

    def plan(self, intake: NormalizedIntake, strategy: StrategyPlan) -> AdapterPlan:
        steps = [
            "Resolve app identifier or package artifact",
            "Validate launch and entry-point smoke flow",
            "Evaluate permissions/auth config in skeleton mode",
            "Collect logs and traces",
        ]
        return AdapterPlan(steps=steps, coverage=strategy.coverage, metadata={"feature": intake.feature})

    def generate_assets(self, intake: NormalizedIntake, adapter_plan: AdapterPlan) -> GeneratedAssets:
        return GeneratedAssets(
            artifacts=["mobile-smoke-skeleton"],
            metadata={"step_count": len(adapter_plan.steps)},
        )

    def execute(self, intake: NormalizedIntake, generated_assets: GeneratedAssets) -> ExecutionResult:
        app_id = str(intake.request.get("app_id") or intake.environment.get("app_id") or "").strip()
        entry_points = intake.entry_points or intake.request.get("entry_points", [])
        permissions = intake.request.get("permissions") or intake.environment.get("permissions") or []
        artifact_paths = [artifact.path for artifact in intake.artifacts if artifact.path]
        runner_result = run_mobile_smoke(
            app_identifier=app_id,
            entry_points=[item for item in entry_points if isinstance(item, dict)],
            permissions=[str(item) for item in permissions] if isinstance(permissions, list) else [],
            auth_required=bool(intake.auth.get("required", False)),
            artifacts=artifact_paths,
            evidence_dir=self.config.paths.evidence_dir,
        )
        return ExecutionResult(
            status=runner_result.get("status", "failed"),
            summary=runner_result.get("summary", {}),
            coverage=runner_result.get("coverage", {}),
            defect_details=runner_result.get("defects", []),
            evidence=runner_result.get("evidence", {}),
            recommendation_notes=runner_result.get("recommendation_notes", []),
            raw_output=runner_result.get("raw_output", {}),
        )

    def collect_evidence(self, intake: NormalizedIntake, execution_result: ExecutionResult) -> EvidenceBundle:
        evidence = execution_result.evidence.model_copy(deep=True)
        evidence.logs.append(f"Adapter={self.name}; status={execution_result.status}; skeleton=true")
        return evidence
