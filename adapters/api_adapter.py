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
from runners.pytest_runner import run_api_pytest


class ApiAdapter(BaseAdapter):
    name = "api"

    def discover(self, intake: NormalizedIntake) -> DiscoveryResult:
        base_url = intake.api.get("base_url") or intake.environment.get("base_url") or intake.target or ""
        endpoints = intake.request.get("endpoints", [])
        return DiscoveryResult(items=[base_url, *[str(endpoint) for endpoint in endpoints]], metadata={"adapter": self.name})

    def plan(self, intake: NormalizedIntake, strategy: StrategyPlan) -> AdapterPlan:
        steps = [
            "Resolve API base URL",
            "Generate temporary pytest smoke test",
            "Execute pytest against configured endpoints",
            "Collect pytest logs as evidence",
        ]
        return AdapterPlan(steps=steps, coverage=strategy.coverage, metadata={"feature": intake.feature})

    def generate_assets(self, intake: NormalizedIntake, adapter_plan: AdapterPlan) -> GeneratedAssets:
        endpoints = intake.request.get("endpoints", ["/"])
        return GeneratedAssets(
            artifacts=["api-smoke-pytest"],
            metadata={"endpoint_count": len(endpoints), "step_count": len(adapter_plan.steps)},
        )

    def execute(self, intake: NormalizedIntake, generated_assets: GeneratedAssets) -> ExecutionResult:
        base_url = intake.api.get("base_url") or intake.environment.get("base_url") or intake.target or ""
        endpoints = intake.request.get("endpoints", ["/"])
        environment_auth = intake.environment.get("auth", {})
        auth_config = intake.auth if intake.auth else environment_auth if isinstance(environment_auth, dict) else {}
        required_fields = intake.request.get("required_fields", {})
        negative_cases = intake.request.get("negative_cases", [])
        runner_result = run_api_pytest(
            base_url=base_url,
            endpoints=endpoints,
            timeout_s=self.config.timeouts.api_s,
            pytest_args=self.config.runners.api.pytest_args,
            auth=auth_config if isinstance(auth_config, dict) else {},
            required_fields=required_fields if isinstance(required_fields, dict) else {},
            negative_cases=negative_cases if isinstance(negative_cases, list) else [],
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
