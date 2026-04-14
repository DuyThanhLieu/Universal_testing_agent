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
from runners.playwright_runner import run_web_smoke


class WebAdapter(BaseAdapter):
    name = "web"

    def discover(self, intake: NormalizedIntake) -> DiscoveryResult:
        return DiscoveryResult(items=[intake.target or ""], metadata={"adapter": self.name})

    def plan(self, intake: NormalizedIntake, strategy: StrategyPlan) -> AdapterPlan:
        steps = [
            "Navigate to target URL",
            "Validate HTTP response",
            "Verify auth selector when required",
            "Capture screenshot evidence",
        ]
        return AdapterPlan(steps=steps, coverage=strategy.coverage, metadata={"feature": intake.feature})

    def generate_assets(self, intake: NormalizedIntake, adapter_plan: AdapterPlan) -> GeneratedAssets:
        return GeneratedAssets(artifacts=["web-smoke-run"], metadata={"step_count": len(adapter_plan.steps)})

    def execute(self, intake: NormalizedIntake, generated_assets: GeneratedAssets) -> ExecutionResult:
        request_selectors = intake.request.get("selectors", [])
        selectors: list[str] = []
        if isinstance(request_selectors, list):
            selectors.extend(str(item) for item in request_selectors if str(item).strip())
        auth_selector = str(intake.auth.get("success_selector", "")).strip()
        if auth_selector and bool(intake.auth.get("required", False)):
            selectors.append(auth_selector)
        selectors = list(dict.fromkeys(selectors))

        navigation_paths = intake.request.get("navigation_paths", [])
        if not isinstance(navigation_paths, list):
            navigation_paths = []

        runner_result = run_web_smoke(
            url=intake.target or "",
            auth=intake.auth,
            timeout_ms=self.config.timeouts.web_ms,
            screenshot_dir=self.config.paths.evidence_dir,
            browser=self.config.runners.web.browser,
            headless=self.config.runners.web.headless,
            selectors=selectors,
            navigation_paths=[str(item) for item in navigation_paths if str(item).strip()],
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
