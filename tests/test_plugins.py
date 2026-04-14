from __future__ import annotations

from adapters.base import BaseAdapter
from orchestrator.config import load_runtime_config
from orchestrator.models import (
    AdapterPlan,
    DiscoveryResult,
    EvidenceBundle,
    ExecutionResult,
    GeneratedAssets,
    NormalizedIntake,
    StrategyPlan,
)
from orchestrator.plugin_loader import discover_plugins, validate_plugin
from orchestrator.plugins import AdapterPlugin
from orchestrator.registry import PluginAwareRegistry, get_registry


class DummyAdapter(BaseAdapter):
    name = "dummy"

    def discover(self, intake: NormalizedIntake) -> DiscoveryResult:
        return DiscoveryResult(items=[intake.name], metadata={})

    def plan(self, intake: NormalizedIntake, strategy: StrategyPlan) -> AdapterPlan:
        return AdapterPlan(steps=["x"], coverage={}, metadata={})

    def generate_assets(self, intake: NormalizedIntake, adapter_plan: AdapterPlan) -> GeneratedAssets:
        return GeneratedAssets(artifacts=[], metadata={})

    def execute(self, intake: NormalizedIntake, generated_assets: GeneratedAssets) -> ExecutionResult:
        return ExecutionResult(status="passed")

    def collect_evidence(self, intake: NormalizedIntake, execution_result: ExecutionResult) -> EvidenceBundle:
        return EvidenceBundle(logs=["ok"])


def test_builtin_plugin_discovery_returns_expected_plugins() -> None:
    plugins, errors = discover_plugins()
    names = sorted(plugin.plugin_name for plugin in plugins)
    assert errors == []
    assert names == ["api", "data_pipeline", "llm_app", "mobile", "model", "rag_app", "web", "workflow"]


def test_plugin_validation_rejects_invalid_capability() -> None:
    plugin = AdapterPlugin(
        plugin_name="bad-plugin",
        plugin_version="0.0.1",
        author="tester",
        dependencies=[],
        compatibility={"python": ">=3.11"},
        supported_product_types=["web"],
        supported_capabilities=["not_a_capability"],
        adapter_class=DummyAdapter,
        fallback_mode="native",
        health_metadata={},
    )
    validation = validate_plugin(plugin)
    assert validation.valid is False
    assert any("Unsupported capabilities" in error for error in validation.errors)


def test_registry_duplicate_plugin_name_is_handled() -> None:
    registry = PluginAwareRegistry(include_builtin=False)
    plugin = AdapterPlugin(
        plugin_name="demo-plugin",
        plugin_version="1.0.0",
        author="tester",
        dependencies=[],
        compatibility={"python": ">=3.11"},
        supported_product_types=["web"],
        supported_capabilities=[
            "discovery",
            "classification",
            "planning",
            "asset_generation",
            "contract_validation",
            "execution_smoke",
            "policy_evaluation",
            "history_tracking",
            "trend_analysis",
            "comparison",
            "reporting",
        ],
        adapter_class=DummyAdapter,
        fallback_mode="native",
        health_metadata={},
        discovered_from="test",
    )
    first = registry.register_plugin(plugin)
    second = registry.register_plugin(plugin)
    assert first.validation.valid is True
    assert second.plugin.plugin_name == "demo-plugin"
    assert registry.conflicts()


def test_registry_query_by_capability_and_product_type() -> None:
    registry = get_registry(force_reload=True)
    reporting_plugins = registry.plugins_for_capability("reporting")
    assert "web" in reporting_plugins
    assert "mobile" in registry.plugins_for_product_type("mobile")
    assert "rag_app" in registry.plugins_for_product_type("rag_app")


def test_registry_can_create_adapter_from_plugin() -> None:
    registry = get_registry(force_reload=True)
    config = load_runtime_config()
    adapter = registry.create_adapter("llm_app", config)
    assert adapter.name == "llm_app"


def test_plugin_validation_exposes_support_level_and_missing_capabilities() -> None:
    registry = get_registry(force_reload=True)
    web = registry.inspect_plugin("web")
    mobile = registry.inspect_plugin("mobile")
    assert web is not None
    assert mobile is not None
    assert web.validation.support_level == "full"
    assert mobile.validation.support_level == "fallback_only"
    assert web.validation.missing_recommended_capabilities == []
