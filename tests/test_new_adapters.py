from orchestrator.config import load_runtime_config
from orchestrator.executor import execute_pipeline
from orchestrator.models import Artifact, NormalizedIntake
from orchestrator.planner import generate_test_strategy
from orchestrator.router import select_adapter


def test_mobile_adapter_execution_is_offline_safe() -> None:
    config = load_runtime_config()
    intake = NormalizedIntake(
        manifest_path="manifests/samples/mobile_app_smoke.yaml",
        name="mobile-app-smoke",
        project_type="mobile",
        artifacts=[Artifact(name="meta", type="mobile", path="manifests/samples/mobile_bundle_metadata.json")],
        request={"app_id": "com.example.travel", "permissions": ["camera"]},
        entry_points=[{"name": "home", "route": "home"}],
        acceptance={},
        outputs={},
        auth={"required": True},
        constraints=[],
        api={},
        model={},
    )
    strategy = generate_test_strategy(intake, "mobile")
    adapter = select_adapter("mobile", config)
    envelope = execute_pipeline(intake, "mobile", strategy, adapter)
    assert envelope.adapter == "mobile"
    assert envelope.summary.total_checks >= 1


def test_llm_app_adapter_execution_is_offline_safe() -> None:
    config = load_runtime_config()
    intake = NormalizedIntake(
        manifest_path="manifests/samples/llm_app_eval.yaml",
        name="llm-app-eval",
        project_type="llm_app",
        labels=["safe"],
        artifacts=[Artifact(name="dataset", type="dataset", path="manifests/samples/llm_app_eval_dataset.json")],
        request={
            "tools": ["search"],
            "fallback_strategy": "safe-default",
            "eval_cases": [{"prompt": "hello", "expected_contains": "hello", "mock_response": "hello safe"}],
        },
        acceptance={},
        outputs={},
        auth={},
        constraints=[],
        api={},
        model={},
    )
    strategy = generate_test_strategy(intake, "llm_app")
    adapter = select_adapter("llm_app", config)
    envelope = execute_pipeline(intake, "llm_app", strategy, adapter)
    assert envelope.adapter == "llm_app"
    assert envelope.summary.total_checks >= 1


def test_rag_app_adapter_execution_is_offline_safe() -> None:
    config = load_runtime_config()
    intake = NormalizedIntake(
        manifest_path="manifests/samples/rag_app_eval.yaml",
        name="rag-app-eval",
        project_type="rag_app",
        artifacts=[Artifact(name="corpus", type="corpus", path="manifests/samples/rag_corpus.json")],
        request={
            "require_citations": True,
            "tools": ["vector_search"],
            "fallback_strategy": "safe-no-answer",
            "eval_cases": [
                {
                    "prompt": "refund",
                    "expected_contains": "30 days",
                    "expected_citation": "policy/refund",
                    "mock_response": "30 days [policy/refund]",
                }
            ],
        },
        acceptance={},
        outputs={},
        auth={},
        constraints=[],
        api={},
        model={},
    )
    strategy = generate_test_strategy(intake, "rag_app")
    adapter = select_adapter("rag_app", config)
    envelope = execute_pipeline(intake, "rag_app", strategy, adapter)
    assert envelope.adapter == "rag_app"
    assert envelope.summary.total_checks >= 1


def test_workflow_adapter_execution_is_offline_safe() -> None:
    config = load_runtime_config()
    intake = NormalizedIntake(
        manifest_path="manifests/samples/workflow_smoke.yaml",
        name="workflow-smoke",
        project_type="workflow",
        request={
            "trigger_payload": {"idempotency_key": "wf-key"},
            "steps": [{"id": "s1"}],
            "transitions": [{"from": "s1", "to": "s2"}],
            "retry_policy": {"idempotent": True},
        },
        acceptance={},
        outputs={},
        auth={},
        constraints=[],
        api={},
        model={},
    )
    strategy = generate_test_strategy(intake, "workflow")
    adapter = select_adapter("workflow", config)
    envelope = execute_pipeline(intake, "workflow", strategy, adapter)
    assert envelope.adapter == "workflow"
    assert envelope.summary.total_checks >= 1


def test_data_pipeline_adapter_execution_is_offline_safe() -> None:
    config = load_runtime_config()
    intake = NormalizedIntake(
        manifest_path="manifests/samples/data_pipeline_validation.yaml",
        name="data-pipeline-validation",
        project_type="data_pipeline",
        artifacts=[
            Artifact(name="schema", type="schema", path="manifests/samples/data_pipeline_schema.json"),
            Artifact(name="batch", type="batch", path="manifests/samples/data_pipeline_batch.json"),
        ],
        request={
            "schema_path": "manifests/samples/data_pipeline_schema.json",
            "batch_path": "manifests/samples/data_pipeline_batch.json",
            "expected_columns": ["id", "event_type", "created_at", "amount"],
            "transformations": ["normalize_amount"],
        },
        acceptance={},
        outputs={},
        auth={},
        constraints=[],
        api={},
        model={},
    )
    strategy = generate_test_strategy(intake, "data_pipeline")
    adapter = select_adapter("data_pipeline", config)
    envelope = execute_pipeline(intake, "data_pipeline", strategy, adapter)
    assert envelope.adapter == "data_pipeline"
    assert envelope.summary.total_checks >= 1
