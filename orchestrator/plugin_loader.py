from __future__ import annotations

import importlib
import os
import re
from typing import Any

from adapters.base import BaseAdapter
from orchestrator.capabilities import CORE_CAPABILITIES, capability_names
from orchestrator.plugins import AdapterPlugin, PluginValidationResult, get_builtin_adapter_plugins

VALID_PRODUCT_TYPES: set[str] = {
    "web",
    "api",
    "model",
    "mobile",
    "llm_app",
    # future-friendly taxonomy targets
    "chatbot",
    "rag_app",
    "workflow",
    "desktop_app",
    "browser_extension",
    "database",
    "data_pipeline",
}

VALID_FALLBACK_MODES: set[str] = {"native", "skeleton_smoke", "simulated", "deferred", "disabled"}
REQUIRED_ADAPTER_METHODS: tuple[str, ...] = ("discover", "plan", "generate_assets", "execute", "collect_evidence")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def _normalize_module_paths(module_paths: list[str] | None = None) -> list[str]:
    explicit = module_paths or []
    env_paths = [item.strip() for item in os.getenv("UTA_PLUGIN_MODULES", "").split(",") if item.strip()]
    seen: set[str] = set()
    ordered: list[str] = []
    for path in [*explicit, *env_paths]:
        if path not in seen:
            ordered.append(path)
            seen.add(path)
    return ordered


def _extract_plugins_from_module(module: Any) -> list[AdapterPlugin]:
    if hasattr(module, "get_plugins") and callable(module.get_plugins):
        raw_plugins = module.get_plugins()
    elif hasattr(module, "PLUGINS"):
        raw_plugins = getattr(module, "PLUGINS")
    else:
        return []

    plugins: list[AdapterPlugin] = []
    for item in raw_plugins or []:
        if isinstance(item, AdapterPlugin):
            plugins.append(item)
        elif isinstance(item, dict):
            plugins.append(AdapterPlugin.model_validate(item))
    return plugins


def discover_plugins(module_paths: list[str] | None = None, include_builtin: bool = True) -> tuple[list[AdapterPlugin], list[str]]:
    plugins: list[AdapterPlugin] = []
    errors: list[str] = []

    if include_builtin:
        plugins.extend(get_builtin_adapter_plugins())

    for module_path in _normalize_module_paths(module_paths):
        try:
            module = importlib.import_module(module_path)
            discovered = _extract_plugins_from_module(module)
            for plugin in discovered:
                plugin.discovered_from = module_path
            plugins.extend(discovered)
        except Exception as exc:
            errors.append(f"Failed to load plugin module '{module_path}': {exc}")

    return plugins, errors


def _adapter_method_coverage(adapter_class: type[Any]) -> list[str]:
    covered: list[str] = []
    for method_name in REQUIRED_ADAPTER_METHODS:
        method = getattr(adapter_class, method_name, None)
        if callable(method):
            covered.append(method_name)
    return covered


def validate_plugin(plugin: AdapterPlugin) -> PluginValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not plugin.plugin_name.strip():
        errors.append("plugin_name is required.")
    if not plugin.plugin_version.strip():
        errors.append("plugin_version is required.")
    if not plugin.supported_product_types:
        errors.append("supported_product_types must not be empty.")
    if not plugin.supported_capabilities:
        errors.append("supported_capabilities must not be empty.")
    if not SEMVER_PATTERN.match(plugin.plugin_version):
        errors.append("plugin_version must follow semantic versioning (e.g. 1.8.0).")
    if not plugin.author.strip():
        errors.append("author is required.")
    if not isinstance(plugin.dependencies, list):
        errors.append("dependencies must be a list of package specifiers.")
    if not isinstance(plugin.compatibility, dict):
        errors.append("compatibility must be a dictionary.")
    elif "python" not in plugin.compatibility:
        warnings.append("compatibility.python is not declared.")
    elif not str(plugin.compatibility.get("python", "")).strip():
        errors.append("compatibility.python must not be empty.")

    invalid_product_types = sorted(set(plugin.supported_product_types) - VALID_PRODUCT_TYPES)
    if invalid_product_types:
        errors.append(f"Unsupported product types: {', '.join(invalid_product_types)}")

    known_capabilities = set(capability_names(CORE_CAPABILITIES))
    invalid_capabilities = sorted(set(plugin.supported_capabilities) - known_capabilities)
    if invalid_capabilities:
        errors.append(f"Unsupported capabilities: {', '.join(invalid_capabilities)}")

    adapter_class = plugin.adapter_class
    if not isinstance(adapter_class, type) or not issubclass(adapter_class, BaseAdapter):
        errors.append("adapter_class must inherit from BaseAdapter.")
        adapter_coverage: list[str] = []
    else:
        adapter_coverage = _adapter_method_coverage(adapter_class)
        missing_methods = sorted(set(REQUIRED_ADAPTER_METHODS) - set(adapter_coverage))
        if missing_methods:
            errors.append(f"adapter_class missing required methods: {', '.join(missing_methods)}")

    if plugin.fallback_mode not in VALID_FALLBACK_MODES:
        errors.append(f"Invalid fallback_mode '{plugin.fallback_mode}'.")

    core_capabilities = set(capability_names(CORE_CAPABILITIES))
    missing_capabilities = sorted(core_capabilities - set(plugin.supported_capabilities))
    coverage = 0.0
    if core_capabilities:
        coverage = round(len(set(plugin.supported_capabilities) & core_capabilities) / len(core_capabilities), 4)
    if coverage < 1.0:
        warnings.append("Plugin does not cover all core capabilities.")

    support_level = "partial"
    if len(errors) == 0 and plugin.fallback_mode == "native" and coverage >= 1.0:
        support_level = "full"
    elif len(errors) == 0 and plugin.fallback_mode != "native":
        support_level = "fallback_only"

    fallback_note = plugin.health_metadata.get("fallback_note")
    if fallback_note is not None and not isinstance(fallback_note, str):
        fallback_note = str(fallback_note)

    return PluginValidationResult(
        plugin_name=plugin.plugin_name,
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        adapter_method_coverage=adapter_coverage,
        capability_completeness=coverage,
        missing_recommended_capabilities=missing_capabilities,
        support_level=support_level,
        fallback_support_note=fallback_note,
    )
