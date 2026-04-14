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
from runners.model_runner import run_model_evaluation


class ModelAdapter(BaseAdapter):
    name = "model"

    def discover(self, intake: NormalizedIntake) -> DiscoveryResult:
        endpoint = intake.model.get("endpoint") or intake.request.get("model_endpoint") or intake.target or ""
        return DiscoveryResult(items=[endpoint], metadata={"adapter": self.name})

    def plan(self, intake: NormalizedIntake, strategy: StrategyPlan) -> AdapterPlan:
        steps = [
            "Resolve model endpoint",
            "Build evaluation prompts",
            "Execute evaluator against endpoint",
            "Compute quality score against threshold",
        ]
        return AdapterPlan(steps=steps, coverage=strategy.coverage, metadata={"feature": intake.feature})

    def generate_assets(self, intake: NormalizedIntake, adapter_plan: AdapterPlan) -> GeneratedAssets:
        cases = intake.request.get("eval_cases") or [{"prompt": "Ping", "expected_contains": "pong"}]
        return GeneratedAssets(
            artifacts=["model-eval"],
            metadata={"case_count": len(cases), "step_count": len(adapter_plan.steps)},
        )

    def execute(self, intake: NormalizedIntake, generated_assets: GeneratedAssets) -> ExecutionResult:
        endpoint = intake.model.get("endpoint") or intake.request.get("model_endpoint") or intake.target or ""
        eval_cases = intake.request.get("eval_cases") or [{"prompt": "Ping", "expected_contains": "pong"}]
        dataset_path = str(intake.request.get("dataset_path", "")).strip() or None
        for artifact in intake.artifacts:
            if artifact.path and ("dataset" in artifact.type.lower() or "sample" in artifact.type.lower()):
                dataset_path = artifact.path
                break

        threshold = float(intake.acceptance.get("quality_threshold", self.config.runners.model.default_threshold))
        runner_result = run_model_evaluation(
            endpoint=endpoint,
            eval_cases=eval_cases,
            timeout_s=self.config.timeouts.model_s,
            threshold=threshold,
            labels=intake.labels,
            dataset_path=dataset_path,
            dataset_samples=intake.request.get("dataset_samples", []),
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
        evidence.logs.append(f"Adapter={self.name}; status={execution_result.status}")
        return evidence
