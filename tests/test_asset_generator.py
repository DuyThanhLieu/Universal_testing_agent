from pathlib import Path

from orchestrator.asset_generator import generate_assets
from orchestrator.config import load_runtime_config
from orchestrator.models import Artifact, NormalizedIntake, StrategyPlan


def _intake(project_type: str) -> NormalizedIntake:
    return NormalizedIntake(
        manifest_path=f"manifests/samples/{project_type}.yaml",
        name=f"{project_type}-project",
        project_type=project_type,
        labels=["safe"] if project_type == "model" else [],
        artifacts=[Artifact(name="spec", type="openapi", path="openapi.yaml")] if project_type == "api" else [],
        environment={},
        request={"endpoints": ["/health"]} if project_type == "api" else {},
        acceptance={},
        outputs={},
        auth={},
        constraints=[],
        api={},
        model={},
    )


def test_generate_assets_writes_expected_files_for_web() -> None:
    config = load_runtime_config()
    intake = _intake("web")
    strategy = StrategyPlan(scope=["x"], risks=["y"], coverage={}, execution_priorities=["P0"])
    bundle = generate_assets(intake, "web", strategy, config)
    assert bundle.artifact_paths
    assert Path("results/checklist_latest.json").exists()
    assert Path("results/testcases_latest.md").exists()
    assert Path("results/bug_report_template.md").exists()


def test_generate_assets_varies_by_product_type() -> None:
    config = load_runtime_config()
    api_bundle = generate_assets(_intake("api"), "api", StrategyPlan(endpoint_matrix_summary=[{"endpoint": "/x"}]), config)
    model_bundle = generate_assets(
        _intake("model"),
        "model",
        StrategyPlan(evaluation_dimensions=["d1"], metrics_to_compute=["m1"]),
        config,
    )
    assert any(item["id"].startswith("API-") for item in api_bundle.checklist)
    assert any(item["id"].startswith("MOD-") for item in model_bundle.checklist)


def test_generate_assets_supports_mobile_and_llm_app() -> None:
    config = load_runtime_config()
    mobile_bundle = generate_assets(
        _intake("mobile"),
        "mobile",
        StrategyPlan(coverage_focus=["navigation", "permissions"]),
        config,
    )
    llm_bundle = generate_assets(
        _intake("llm_app"),
        "llm_app",
        StrategyPlan(capability_expectations=["reporting"], evaluation_dimensions=["safety"]),
        config,
    )
    assert any(item["id"].startswith("MOB-") for item in mobile_bundle.checklist)
    assert any(item["id"].startswith("LLM-") for item in llm_bundle.checklist)


def test_generate_assets_supports_rag_workflow_data_pipeline() -> None:
    config = load_runtime_config()
    rag_bundle = generate_assets(
        _intake("rag_app"),
        "rag_app",
        StrategyPlan(coverage_focus=["grounding", "citation"]),
        config,
    )
    workflow_bundle = generate_assets(
        _intake("workflow"),
        "workflow",
        StrategyPlan(execution_priorities=["P0: trigger"]),
        config,
    )
    pipeline_bundle = generate_assets(
        _intake("data_pipeline"),
        "data_pipeline",
        StrategyPlan(coverage_focus=["schema", "integrity"]),
        config,
    )
    assert any(item["id"].startswith("RAG-") for item in rag_bundle.checklist)
    assert any(item["id"].startswith("WF-") for item in workflow_bundle.checklist)
    assert any(item["id"].startswith("DP-") for item in pipeline_bundle.checklist)
