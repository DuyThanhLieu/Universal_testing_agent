from pathlib import Path

from runners.data_pipeline_runner import run_data_pipeline_smoke
from runners.model_runner import run_model_evaluation
from runners.pytest_runner import run_api_pytest
from runners.rag_app_runner import run_rag_app_smoke
from runners.playwright_runner import run_web_smoke


def _assert_defect_shape(defect: dict) -> None:
    assert "severity" in defect
    assert "category" in defect
    assert "reproducibility" in defect
    assert "confidence_score" in defect


def test_web_runner_depth_outputs_structured_defects(tmp_path: Path) -> None:
    result = run_web_smoke(
        url="",
        auth={},
        timeout_ms=100,
        screenshot_dir=str(tmp_path),
        selectors=["html"],
        navigation_paths=["/"],
    )
    assert result["summary"]["total_checks"] >= 1
    assert result["defects"]
    _assert_defect_shape(result["defects"][0])


def test_api_runner_depth_supports_required_fields_and_negative_cases() -> None:
    result = run_api_pytest(
        base_url="",
        endpoints=[{"path": "/store/items", "expected_status": 200}],
        timeout_s=1,
        pytest_args=[],
        auth={"type": "basic"},
        required_fields={"/store/items": ["id", "event_type"]},
        negative_cases=[{"endpoint": "/store/items", "expected_status": 400}],
    )
    assert result["summary"]["total_checks"] >= 2
    assert "raw_output" in result


def test_model_runner_depth_computes_metrics() -> None:
    result = run_model_evaluation(
        endpoint="",
        eval_cases=[],
        timeout_s=1,
        threshold=0.5,
        labels=["safe", "unsafe"],
        dataset_samples=[
            {"expected_label": "safe", "predicted": "safe"},
            {"expected_label": "unsafe", "predicted": "unsafe"},
            {"expected_label": "unsafe", "predicted": "safe"},
        ],
    )
    metrics = result["raw_output"]["metrics"]
    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics


def test_rag_runner_depth_checks_grounding_and_hallucination() -> None:
    result = run_rag_app_smoke(
        eval_cases=[
            {
                "prompt": "refund policy",
                "expected_contains": "30 days",
                "expected_reference": "policy/refund",
                "mock_response": "30 days [policy/refund]",
                "context_hit": True,
            }
        ],
        corpus_path="manifests/samples/rag_corpus.json",
        require_citations=True,
        tool_names=["vector_search"],
        fallback_strategy="safe-no-answer",
        evidence_dir="evidence",
    )
    assert result["summary"]["total_checks"] >= 1


def test_data_pipeline_runner_depth_checks_batch_completeness() -> None:
    result = run_data_pipeline_smoke(
        schema_path="manifests/samples/data_pipeline_schema.json",
        batch_path="manifests/samples/data_pipeline_batch.json",
        expected_columns=["id", "event_type", "created_at", "amount"],
        transformations=["normalize_amount"],
        evidence_dir="evidence",
        expected_batch_size=2,
    )
    assert result["summary"]["total_checks"] >= 1
    assert result["status"] in {"passed", "failed", "blocked"}
