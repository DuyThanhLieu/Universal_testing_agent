from orchestrator.config import load_runtime_config
from orchestrator.registry import get_registry


def test_registry_supports_all_v17_product_types() -> None:
    registry = get_registry()
    assert registry.supported_product_types() == [
        "api",
        "data_pipeline",
        "llm_app",
        "mobile",
        "model",
        "rag_app",
        "web",
        "workflow",
    ]


def test_registry_returns_skeleton_fallback_mode_for_mobile_and_llm_app() -> None:
    registry = get_registry()
    assert registry.fallback_mode_for("mobile") == "skeleton_smoke"
    assert registry.fallback_mode_for("llm_app") == "skeleton_smoke"
    assert registry.fallback_mode_for("rag_app") == "skeleton_smoke"
    assert registry.fallback_mode_for("workflow") == "skeleton_smoke"
    assert registry.fallback_mode_for("data_pipeline") == "skeleton_smoke"


def test_registry_falls_back_for_unknown_product_type() -> None:
    registry = get_registry()
    config = load_runtime_config()
    adapter = registry.create_adapter("desktop", config)
    assert adapter.name == "web"
    assert "unsupported_product_type" in registry.fallback_mode_for("desktop")
