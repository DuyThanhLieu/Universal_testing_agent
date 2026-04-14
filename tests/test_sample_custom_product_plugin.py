from orchestrator.registry import get_registry


def test_sample_custom_product_plugin_placeholder() -> None:
    registry = get_registry()
    # Replace with concrete plugin tests after registration.
    assert isinstance(registry.plugins_for_capability("reporting"), list)
