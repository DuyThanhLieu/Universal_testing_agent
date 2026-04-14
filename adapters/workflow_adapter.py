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
from runners.workflow_runner import run_workflow_smoke


class WorkflowAdapter(BaseAdapter):
    name = "workflow"

    def discover(self, intake: NormalizedIntake) -> DiscoveryResult:
        steps = intake.request.get("steps", [])
        transitions = intake.request.get("transitions", [])
        return DiscoveryResult(
            items=[str(len(steps)), str(len(transitions))],
            metadata={"adapter": self.name},
        )

    def plan(self, intake: NormalizedIntake, strategy: StrategyPlan) -> AdapterPlan:
        steps = [
            "Validate trigger/input payload",
            "Validate step chaining and transitions",
            "Validate error recovery and idempotency basics",
            "Collect deterministic workflow evidence",
        ]
        return AdapterPlan(steps=steps, coverage=strategy.coverage, metadata={"feature": intake.feature})

    def generate_assets(self, intake: NormalizedIntake, adapter_plan: AdapterPlan) -> GeneratedAssets:
        return GeneratedAssets(
            artifacts=["workflow-smoke-skeleton"],
            metadata={"step_count": len(adapter_plan.steps)},
        )

    def execute(self, intake: NormalizedIntake, generated_assets: GeneratedAssets) -> ExecutionResult:
        runner_result = run_workflow_smoke(
            trigger_payload=intake.request.get("trigger_payload", {})
            if isinstance(intake.request.get("trigger_payload", {}), dict)
            else {},
            steps=[item for item in intake.request.get("steps", []) if isinstance(item, dict)]
            if isinstance(intake.request.get("steps", []), list)
            else [],
            transitions=[item for item in intake.request.get("transitions", []) if isinstance(item, dict)]
            if isinstance(intake.request.get("transitions", []), list)
            else [],
            retry_policy=intake.request.get("retry_policy", {})
            if isinstance(intake.request.get("retry_policy", {}), dict)
            else {},
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
