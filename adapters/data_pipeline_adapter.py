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
from runners.data_pipeline_runner import run_data_pipeline_smoke


class DataPipelineAdapter(BaseAdapter):
    name = "data_pipeline"

    def discover(self, intake: NormalizedIntake) -> DiscoveryResult:
        schema_path = str(intake.request.get("schema_path", "")).strip()
        batch_path = str(intake.request.get("batch_path", "")).strip()
        if not schema_path or not batch_path:
            for artifact in intake.artifacts:
                artifact_type = artifact.type.lower()
                if artifact.path and "schema" in artifact_type and not schema_path:
                    schema_path = artifact.path
                if artifact.path and "batch" in artifact_type and not batch_path:
                    batch_path = artifact.path
        return DiscoveryResult(items=[schema_path, batch_path], metadata={"adapter": self.name})

    def plan(self, intake: NormalizedIntake, strategy: StrategyPlan) -> AdapterPlan:
        steps = [
            "Load schema and sample batch artifacts",
            "Validate schema consistency and data integrity baselines",
            "Validate transformation declarations and batch handling expectations",
            "Collect deterministic pipeline traces",
        ]
        return AdapterPlan(steps=steps, coverage=strategy.coverage, metadata={"feature": intake.feature})

    def generate_assets(self, intake: NormalizedIntake, adapter_plan: AdapterPlan) -> GeneratedAssets:
        return GeneratedAssets(
            artifacts=["data-pipeline-smoke-skeleton"],
            metadata={"step_count": len(adapter_plan.steps)},
        )

    def execute(self, intake: NormalizedIntake, generated_assets: GeneratedAssets) -> ExecutionResult:
        schema_path = str(intake.request.get("schema_path", "")).strip() or None
        batch_path = str(intake.request.get("batch_path", "")).strip() or None
        if not schema_path or not batch_path:
            for artifact in intake.artifacts:
                artifact_type = artifact.type.lower()
                if artifact.path and "schema" in artifact_type and not schema_path:
                    schema_path = artifact.path
                if artifact.path and "batch" in artifact_type and not batch_path:
                    batch_path = artifact.path

        expected_columns = intake.request.get("expected_columns", [])
        transformations = intake.request.get("transformations", [])
        expected_batch_size = intake.request.get("expected_batch_size")
        runner_result = run_data_pipeline_smoke(
            schema_path=schema_path,
            batch_path=batch_path,
            expected_columns=[str(item) for item in expected_columns] if isinstance(expected_columns, list) else [],
            transformations=[str(item) for item in transformations] if isinstance(transformations, list) else [],
            evidence_dir=self.config.paths.evidence_dir,
            expected_batch_size=int(expected_batch_size) if expected_batch_size is not None else None,
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
