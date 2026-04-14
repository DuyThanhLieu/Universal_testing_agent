from pathlib import Path

import pytest

from orchestrator.intake import load_manifest


def test_load_manifest_valid_sample() -> None:
    sample_path = Path("manifests/samples/web_booking.yaml")
    manifest = load_manifest(sample_path)
    assert manifest.project_type == "web"
    assert manifest.outputs["report_format"] == "json"


def test_load_manifest_valid_api_and_model_samples() -> None:
    api_manifest = load_manifest(Path("manifests/samples/api_verify_store.yaml"))
    model_manifest = load_manifest(Path("manifests/samples/model_basalt.yaml"))
    assert api_manifest.project_type == "api"
    assert model_manifest.project_type == "model"


def test_load_manifest_v2_mobile_and_llm_app_samples() -> None:
    mobile_manifest = load_manifest(Path("manifests/samples/mobile_app_smoke.yaml"))
    llm_manifest = load_manifest(Path("manifests/samples/llm_app_eval.yaml"))
    assert mobile_manifest.project_type == "mobile"
    assert mobile_manifest.name == "mobile-app-smoke"
    assert llm_manifest.project_type == "llm_app"
    assert llm_manifest.name == "llm-app-eval"


def test_load_manifest_v2_rag_workflow_pipeline_samples() -> None:
    rag_manifest = load_manifest(Path("manifests/samples/rag_app_eval.yaml"))
    workflow_manifest = load_manifest(Path("manifests/samples/workflow_smoke.yaml"))
    pipeline_manifest = load_manifest(Path("manifests/samples/data_pipeline_validation.yaml"))
    assert rag_manifest.project_type == "rag_app"
    assert workflow_manifest.project_type == "workflow"
    assert pipeline_manifest.project_type == "data_pipeline"


def test_load_manifest_missing_required_sections(tmp_path: Path) -> None:
    invalid_manifest = tmp_path / "invalid.yaml"
    invalid_manifest.write_text(
        """
name: invalid
project_type: web
artifacts: []
environment: {}
request: {}
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_manifest(invalid_manifest)
