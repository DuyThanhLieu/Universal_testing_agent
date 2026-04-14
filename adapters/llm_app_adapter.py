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
from runners.llm_app_runner import run_llm_app_smoke


class LlmAppAdapter(BaseAdapter):
    name = "llm_app"

    def discover(self, intake: NormalizedIntake) -> DiscoveryResult:
        tool_names = intake.request.get("tools", [])
        dataset_paths = [artifact.path for artifact in intake.artifacts if artifact.path]
        return DiscoveryResult(
            items=[*[str(item) for item in tool_names], *[path for path in dataset_paths if path]],
            metadata={"adapter": self.name, "labels": intake.labels},
        )

    def plan(self, intake: NormalizedIntake, strategy: StrategyPlan) -> AdapterPlan:
        steps = [
            "Resolve prompt/eval cases and response expectations",
            "Evaluate quality/safety/tool-readiness dimensions",
            "Validate fallback strategy handling",
            "Collect deterministic evidence and metrics",
        ]
        return AdapterPlan(steps=steps, coverage=strategy.coverage, metadata={"feature": intake.feature})

    def generate_assets(self, intake: NormalizedIntake, adapter_plan: AdapterPlan) -> GeneratedAssets:
        eval_cases = intake.request.get("eval_cases", [])
        return GeneratedAssets(
            artifacts=["llm-app-smoke-skeleton"],
            metadata={"step_count": len(adapter_plan.steps), "eval_case_count": len(eval_cases)},
        )

    def execute(self, intake: NormalizedIntake, generated_assets: GeneratedAssets) -> ExecutionResult:
        eval_cases = intake.request.get("eval_cases", [])
        dataset_path = str(intake.request.get("dataset_path", "")).strip() or None
        if not dataset_path:
            for artifact in intake.artifacts:
                if artifact.path and ("dataset" in artifact.type.lower() or "sample" in artifact.type.lower()):
                    dataset_path = artifact.path
                    break
        fallback_strategy = str(intake.request.get("fallback_strategy", "")).strip()
        tool_names = intake.request.get("tools", [])
        runner_result = run_llm_app_smoke(
            eval_cases=[item for item in eval_cases if isinstance(item, dict)],
            labels=intake.labels,
            dataset_path=dataset_path,
            tool_names=[str(item) for item in tool_names] if isinstance(tool_names, list) else [],
            fallback_strategy=fallback_strategy,
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
