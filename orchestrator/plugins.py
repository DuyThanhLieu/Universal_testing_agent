from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from adapters.api_adapter import ApiAdapter
from adapters.base import BaseAdapter
from adapters.data_pipeline_adapter import DataPipelineAdapter
from adapters.llm_app_adapter import LlmAppAdapter
from adapters.mobile_adapter import MobileAdapter
from adapters.model_adapter import ModelAdapter
from adapters.rag_app_adapter import RagAppAdapter
from adapters.web_adapter import WebAdapter
from adapters.workflow_adapter import WorkflowAdapter
from orchestrator.capabilities import CORE_CAPABILITIES, capability_names


class AdapterPlugin(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    plugin_name: str
    plugin_version: str
    author: str = "UTA Team"
    dependencies: list[str] = Field(default_factory=list)
    compatibility: dict[str, Any] = Field(default_factory=dict)
    supported_product_types: list[str] = Field(default_factory=list)
    supported_capabilities: list[str] = Field(default_factory=list)
    adapter_class: type[BaseAdapter]
    fallback_mode: str = "native"
    health_metadata: dict[str, Any] = Field(default_factory=dict)
    discovered_from: str = "builtin"

    def adapter_target(self) -> str:
        return self.adapter_class.__name__


class PluginValidationResult(BaseModel):
    plugin_name: str
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    adapter_method_coverage: list[str] = Field(default_factory=list)
    capability_completeness: float = 0.0
    missing_recommended_capabilities: list[str] = Field(default_factory=list)
    support_level: str = "partial"
    fallback_support_note: str | None = None


class PluginInspection(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    plugin: AdapterPlugin
    validation: PluginValidationResult

    def summary(self) -> dict[str, Any]:
        return {
            "plugin_name": self.plugin.plugin_name,
            "plugin_version": self.plugin.plugin_version,
            "author": self.plugin.author,
            "dependencies": self.plugin.dependencies,
            "compatibility": self.plugin.compatibility,
            "product_types": self.plugin.supported_product_types,
            "capabilities": self.plugin.supported_capabilities,
            "fallback_mode": self.plugin.fallback_mode,
            "adapter_target": self.plugin.adapter_target(),
            "valid": self.validation.valid,
            "warnings": self.validation.warnings,
            "discovered_from": self.plugin.discovered_from,
        }


def _builtin_plugin(
    name: str,
    adapter_class: type[BaseAdapter],
    product_type: str,
    *,
    fallback_mode: str = "native",
    fallback_note: str | None = None,
) -> AdapterPlugin:
    health_metadata: dict[str, Any] = {"origin": "builtin", "adapter": adapter_class.__name__}
    if fallback_note:
        health_metadata["fallback_note"] = fallback_note
    return AdapterPlugin(
        plugin_name=name,
        plugin_version="1.8.0",
        author="UTA Core Team",
        dependencies=["requests>=2.31"],
        compatibility={"python": ">=3.11,<3.13", "uta": ">=1.8.0"},
        supported_product_types=[product_type],
        supported_capabilities=capability_names(CORE_CAPABILITIES),
        adapter_class=adapter_class,
        fallback_mode=fallback_mode,
        health_metadata=health_metadata,
        discovered_from="builtin",
    )


def get_builtin_adapter_plugins() -> list[AdapterPlugin]:
    return [
        _builtin_plugin("web", WebAdapter, "web"),
        _builtin_plugin("api", ApiAdapter, "api"),
        _builtin_plugin("model", ModelAdapter, "model"),
        _builtin_plugin(
            "mobile",
            MobileAdapter,
            "mobile",
            fallback_mode="skeleton_smoke",
            fallback_note="Mobile plugin executes deterministic skeleton smoke checks in v1.8.",
        ),
        _builtin_plugin(
            "llm_app",
            LlmAppAdapter,
            "llm_app",
            fallback_mode="skeleton_smoke",
            fallback_note="llm_app plugin executes deterministic skeleton evaluation in v1.8.",
        ),
        _builtin_plugin(
            "rag_app",
            RagAppAdapter,
            "rag_app",
            fallback_mode="skeleton_smoke",
            fallback_note="rag_app plugin executes deterministic retrieval smoke evaluation in v1.8.",
        ),
        _builtin_plugin(
            "workflow",
            WorkflowAdapter,
            "workflow",
            fallback_mode="skeleton_smoke",
            fallback_note="workflow plugin executes deterministic orchestration smoke validation in v1.8.",
        ),
        _builtin_plugin(
            "data_pipeline",
            DataPipelineAdapter,
            "data_pipeline",
            fallback_mode="skeleton_smoke",
            fallback_note="data_pipeline plugin executes deterministic schema/integrity smoke validation in v1.8.",
        ),
    ]
