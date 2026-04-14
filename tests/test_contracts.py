from pathlib import Path

from orchestrator.contracts import validate_contracts


def test_validate_contracts_for_api_manifest() -> None:
    result = validate_contracts(Path("manifests/samples/api_verify_store.yaml"))
    assert result.verdict in {"pass", "fail"}
    assert "result_contract_basics" in result.checks


def test_validate_contracts_for_model_manifest() -> None:
    result = validate_contracts(Path("manifests/samples/model_basalt.yaml"))
    assert "model_contract_basics" in result.checks


def test_validate_contracts_for_mobile_and_llm_app_manifests() -> None:
    mobile_result = validate_contracts(Path("manifests/samples/mobile_app_smoke.yaml"))
    llm_result = validate_contracts(Path("manifests/samples/llm_app_eval.yaml"))
    assert "mobile_contract_basics" in mobile_result.checks
    assert "llm_app_contract_basics" in llm_result.checks


def test_validate_contracts_for_rag_workflow_and_pipeline_manifests() -> None:
    rag_result = validate_contracts(Path("manifests/samples/rag_app_eval.yaml"))
    workflow_result = validate_contracts(Path("manifests/samples/workflow_smoke.yaml"))
    pipeline_result = validate_contracts(Path("manifests/samples/data_pipeline_validation.yaml"))
    assert "rag_app_contract_basics" in rag_result.checks
    assert "workflow_contract_basics" in workflow_result.checks
    assert "data_pipeline_contract_basics" in pipeline_result.checks
