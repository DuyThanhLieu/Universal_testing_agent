from __future__ import annotations

from adapters.base import BaseAdapter
from orchestrator.models import AdapterPlan, DiscoveryResult, EvidenceBundle, ExecutionResult, GeneratedAssets, NormalizedIntake, StrategyPlan
from runners.sample_custom_product_runner import run_sample_custom_product_smoke


class SampleCustomProductAdapter(BaseAdapter):
    name = "sample_custom_product"

    def discover(self, intake: NormalizedIntake) -> DiscoveryResult:
        return DiscoveryResult(items=[intake.name], metadata={"adapter": self.name})

    def plan(self, intake: NormalizedIntake, strategy: StrategyPlan) -> AdapterPlan:
        return AdapterPlan(steps=["define checks"], coverage=strategy.coverage, metadata={})

    def generate_assets(self, intake: NormalizedIntake, adapter_plan: AdapterPlan) -> GeneratedAssets:
        return GeneratedAssets(artifacts=["sample_custom_product-smoke-skeleton"], metadata={"step_count": len(adapter_plan.steps)})

    def execute(self, intake: NormalizedIntake, generated_assets: GeneratedAssets) -> ExecutionResult:
        runner_result = run_sample_custom_product_smoke(evidence_dir=self.config.paths.evidence_dir)
        return ExecutionResult(
            status=runner_result.get("status", "blocked"),
            summary=runner_result.get("summary", {}),
            coverage=runner_result.get("coverage", {}),
            defect_details=runner_result.get("defects", []),
            evidence=runner_result.get("evidence", {}),
            recommendation_notes=runner_result.get("recommendation_notes", []),
            raw_output=runner_result.get("raw_output", {}),
        )

    def collect_evidence(self, intake: NormalizedIntake, execution_result: ExecutionResult) -> EvidenceBundle:
        evidence = execution_result.evidence.model_copy(deep=True)
        evidence.logs.append(f"Adapter={self.name}; status={execution_result.status}; scaffold=true")
        return evidence
