from orchestrator.classifier import classify_product
from orchestrator.models import Artifact, NormalizedIntake


def _intake(
    *,
    url: str | None = None,
    artifacts: list[Artifact] | None = None,
    project_type: str = "auto",
    model: dict | None = None,
    request: dict | None = None,
    labels: list[str] | None = None,
) -> NormalizedIntake:
    return NormalizedIntake(
        manifest_path="test.yaml",
        name="test",
        project_type=project_type,
        url=url,
        target=url,
        labels=labels or [],
        artifacts=artifacts or [],
        environment={},
        request=request or {},
        acceptance={},
        outputs={},
        auth={},
        constraints=[],
        api={},
        model=model or {},
    )


def test_classifier_detects_web_from_url() -> None:
    intake = _intake(url="https://example.com")
    assert classify_product(intake) == "web"


def test_classifier_detects_api_from_openapi_artifact() -> None:
    intake = _intake(artifacts=[Artifact(name="openapi", type="spec", path="openapi.json")])
    assert classify_product(intake) == "api"


def test_classifier_detects_model_from_endpoint() -> None:
    intake = _intake(model={"endpoint": "https://api.example.com/v1/model"})
    assert classify_product(intake) == "model"


def test_classifier_detects_model_from_labels_hint() -> None:
    intake = _intake(labels=["safe", "unsafe"], request={"goal": "evaluation"})
    assert classify_product(intake) == "model"


def test_classifier_detects_mobile_from_artifact_hint() -> None:
    intake = _intake(
        project_type="auto",
        artifacts=[Artifact(name="android-build", type="apk", path="builds/app.apk")],
        request={"permissions": ["camera"]},
    )
    assert classify_product(intake) == "mobile"


def test_classifier_detects_llm_app_from_prompt_tool_hints() -> None:
    intake = _intake(
        project_type="auto",
        request={"eval_cases": [{"prompt": "help"}], "tools": ["search"], "fallback_strategy": "safe-default"},
        labels=["safe"],
    )
    assert classify_product(intake) == "llm_app"


def test_classifier_detects_rag_app_from_retrieval_citation_hints() -> None:
    intake = _intake(
        project_type="auto",
        request={"goal": "rag evaluation", "require_citations": True, "tools": ["vector_search"]},
        artifacts=[Artifact(name="rag-corpus", type="corpus", path="rag_corpus.json")],
    )
    assert classify_product(intake) == "rag_app"


def test_classifier_detects_workflow_from_trigger_transition_hints() -> None:
    intake = _intake(
        project_type="auto",
        request={"trigger_payload": {"x": 1}, "transitions": [{"from": "a", "to": "b"}], "retry_policy": {"max": 1}},
    )
    assert classify_product(intake) == "workflow"


def test_classifier_detects_data_pipeline_from_schema_batch_hints() -> None:
    intake = _intake(
        project_type="auto",
        request={"expected_columns": ["id"], "transformations": ["normalize"]},
        artifacts=[Artifact(name="schema", type="schema", path="schema.json"), Artifact(name="batch", type="batch", path="batch.json")],
    )
    assert classify_product(intake) == "data_pipeline"
