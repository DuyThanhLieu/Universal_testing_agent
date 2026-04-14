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
from runners.rag_app_runner import run_rag_app_smoke


class RagAppAdapter(BaseAdapter):
    name = "rag_app"

    def discover(self, intake: NormalizedIntake) -> DiscoveryResult:
        tools = intake.request.get("tools", [])
        corpus_path = str(intake.request.get("corpus_path", "")).strip()
        if not corpus_path:
            for artifact in intake.artifacts:
                if artifact.path and ("corpus" in artifact.type.lower() or "dataset" in artifact.type.lower()):
                    corpus_path = artifact.path
                    break
        return DiscoveryResult(
            items=[*[str(item) for item in tools], corpus_path],
            metadata={"adapter": self.name, "require_citations": intake.request.get("require_citations", False)},
        )

    def plan(self, intake: NormalizedIntake, strategy: StrategyPlan) -> AdapterPlan:
        steps = [
            "Resolve retrieval corpus and eval prompts",
            "Validate retrieval grounding and citation expectations",
            "Validate fallback/tool readiness in deterministic mode",
            "Collect logs and traces",
        ]
        return AdapterPlan(steps=steps, coverage=strategy.coverage, metadata={"feature": intake.feature})

    def generate_assets(self, intake: NormalizedIntake, adapter_plan: AdapterPlan) -> GeneratedAssets:
        eval_cases = intake.request.get("eval_cases", [])
        return GeneratedAssets(
            artifacts=["rag-app-smoke-skeleton"],
            metadata={"step_count": len(adapter_plan.steps), "eval_case_count": len(eval_cases)},
        )

    def execute(self, intake: NormalizedIntake, generated_assets: GeneratedAssets) -> ExecutionResult:
        eval_cases = intake.request.get("eval_cases", [])
        corpus_path = str(intake.request.get("corpus_path", "")).strip() or None
        if not corpus_path:
            for artifact in intake.artifacts:
                if artifact.path and ("corpus" in artifact.type.lower() or "dataset" in artifact.type.lower()):
                    corpus_path = artifact.path
                    break
        runner_result = run_rag_app_smoke(
            eval_cases=[item for item in eval_cases if isinstance(item, dict)],
            corpus_path=corpus_path,
            require_citations=bool(intake.request.get("require_citations", False)),
            tool_names=[str(item) for item in intake.request.get("tools", [])]
            if isinstance(intake.request.get("tools", []), list)
            else [],
            fallback_strategy=str(intake.request.get("fallback_strategy", "")).strip(),
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
