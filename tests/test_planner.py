from orchestrator.models import NormalizedIntake
from orchestrator.planner import generate_test_strategy


def test_planner_returns_scope_risks_coverage() -> None:
    intake = NormalizedIntake(
        manifest_path="sample.yaml",
        name="sample",
        project_type="web",
        url="https://example.com",
        target="https://example.com",
        feature="booking",
        labels=[],
        artifacts=[],
        environment={},
        request={},
        acceptance={},
        outputs={},
        auth={},
        constraints=[],
        api={},
        model={},
    )

    plan = generate_test_strategy(intake, "web")
    assert isinstance(plan.scope, list)
    assert isinstance(plan.risks, list)
    assert isinstance(plan.coverage, dict)
    assert plan.execution_priorities


def test_api_plan_includes_endpoint_matrix() -> None:
    intake = NormalizedIntake(
        manifest_path="sample.yaml",
        name="api-sample",
        project_type="api",
        labels=[],
        artifacts=[],
        environment={},
        request={"endpoints": ["/health"]},
        acceptance={},
        outputs={},
        auth={},
        constraints=[],
        api={"base_url": ""},
        model={},
    )
    plan = generate_test_strategy(intake, "api")
    assert plan.endpoint_matrix_summary


def test_model_plan_includes_metrics() -> None:
    intake = NormalizedIntake(
        manifest_path="sample.yaml",
        name="model-sample",
        project_type="model",
        labels=["safe"],
        artifacts=[],
        environment={},
        request={},
        acceptance={},
        outputs={},
        auth={},
        constraints=[],
        api={},
        model={},
    )
    plan = generate_test_strategy(intake, "model")
    assert plan.evaluation_dimensions
    assert plan.metrics_to_compute


def test_mobile_plan_includes_navigation_permission_focus() -> None:
    intake = NormalizedIntake(
        manifest_path="sample.yaml",
        name="mobile-sample",
        project_type="mobile",
        request={"permissions": ["camera"]},
        acceptance={},
        outputs={},
        auth={},
        constraints=[],
        api={},
        model={},
    )
    plan = generate_test_strategy(intake, "mobile")
    assert "navigation" in " ".join(plan.scope).lower()
    assert any("permission" in value.lower() for value in plan.risks)
    assert plan.coverage_focus


def test_llm_app_plan_includes_eval_dimensions() -> None:
    intake = NormalizedIntake(
        manifest_path="sample.yaml",
        name="llm-app-sample",
        project_type="llm_app",
        labels=["safe"],
        request={"eval_cases": [{"prompt": "x"}], "tools": ["search"], "fallback_strategy": "safe-default"},
        acceptance={},
        outputs={},
        auth={},
        constraints=[],
        api={},
        model={},
    )
    plan = generate_test_strategy(intake, "llm_app")
    assert plan.evaluation_dimensions
    assert plan.metrics_to_compute
    assert plan.capability_expectations


def test_rag_app_plan_includes_grounding_and_citation_dimensions() -> None:
    intake = NormalizedIntake(
        manifest_path="sample.yaml",
        name="rag-app-sample",
        project_type="rag_app",
        request={"eval_cases": [{"prompt": "x"}], "require_citations": True, "tools": ["vector_search"]},
        acceptance={},
        outputs={},
        auth={},
        constraints=[],
        api={},
        model={},
    )
    plan = generate_test_strategy(intake, "rag_app")
    assert any("grounding" in item.lower() for item in plan.evaluation_dimensions)
    assert any("citation" in item.lower() for item in plan.evaluation_dimensions)


def test_workflow_plan_includes_transitions_and_recovery_focus() -> None:
    intake = NormalizedIntake(
        manifest_path="sample.yaml",
        name="workflow-sample",
        project_type="workflow",
        request={"steps": [{"id": "a"}], "transitions": [{"from": "a", "to": "b"}], "retry_policy": {"max": 1}},
        acceptance={},
        outputs={},
        auth={},
        constraints=[],
        api={},
        model={},
    )
    plan = generate_test_strategy(intake, "workflow")
    assert "transition" in str(plan.coverage).lower()
    assert any("idempotency" in item.lower() for item in plan.coverage_focus)


def test_data_pipeline_plan_includes_schema_integrity_focus() -> None:
    intake = NormalizedIntake(
        manifest_path="sample.yaml",
        name="pipeline-sample",
        project_type="data_pipeline",
        request={"expected_columns": ["id"], "transformations": ["normalize"]},
        acceptance={},
        outputs={},
        auth={},
        constraints=[],
        api={},
        model={},
    )
    plan = generate_test_strategy(intake, "data_pipeline")
    assert "schema" in str(plan.coverage).lower()
    assert any("integrity" in item.lower() for item in plan.coverage_focus)
