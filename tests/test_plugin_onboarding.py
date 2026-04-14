from pathlib import Path

from orchestrator.plugin_onboarding import evaluate_plugin_onboarding, scaffold_plugin
from orchestrator.registry import get_registry


def test_plugin_onboarding_returns_completeness_payload() -> None:
    registry = get_registry(force_reload=True)
    inspection = registry.inspect_plugin("web")
    assert inspection is not None
    onboarding = evaluate_plugin_onboarding(inspection)
    assert onboarding.plugin_name == "web"
    assert onboarding.onboarding_status in {"ready", "partial", "not_ready"}
    assert 0.0 <= onboarding.completeness_score <= 1.0


def test_scaffold_plugin_creates_expected_files(tmp_path: Path) -> None:
    for folder in ["adapters", "runners", "manifests/samples", "tests"]:
        (tmp_path / folder).mkdir(parents=True, exist_ok=True)
    result = scaffold_plugin("sample_custom_product", mode="generic", project_root=tmp_path)
    assert result["created_files"]
    assert (tmp_path / "adapters" / "sample_custom_product_adapter.py").exists()
    assert (tmp_path / "runners" / "sample_custom_product_runner.py").exists()
    assert (tmp_path / "manifests" / "samples" / "sample_custom_product_sample.yaml").exists()
    assert (tmp_path / "tests" / "test_sample_custom_product_plugin.py").exists()
