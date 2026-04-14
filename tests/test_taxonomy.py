from orchestrator.taxonomy import get_taxonomy_profile, supported_taxonomy_product_types


def test_taxonomy_supports_new_product_types() -> None:
    supported = supported_taxonomy_product_types()
    assert "mobile" in supported
    assert "llm_app" in supported
    assert "rag_app" in supported
    assert "workflow" in supported
    assert "data_pipeline" in supported


def test_taxonomy_profile_contains_dimensions_risks_and_capabilities() -> None:
    profile = get_taxonomy_profile("llm_app")
    assert profile.default_dimensions
    assert profile.default_risks
    assert profile.coverage_focus
    assert "reporting" in profile.capability_expectations
