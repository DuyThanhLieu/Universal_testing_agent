from __future__ import annotations

from collections import defaultdict
from typing import Any

from adapters.base import BaseAdapter
from orchestrator.config import RuntimeConfig
from orchestrator.plugin_loader import discover_plugins, validate_plugin
from orchestrator.plugins import AdapterPlugin, PluginInspection, PluginValidationResult


class PluginAwareRegistry:
    def __init__(self, *, module_paths: list[str] | None = None, include_builtin: bool = True) -> None:
        self._plugin_inspections: dict[str, PluginInspection] = {}
        self._product_type_to_plugin: dict[str, str] = {}
        self._plugins_by_product_type: dict[str, list[str]] = defaultdict(list)
        self._conflicts: list[str] = []
        self._discovery_errors: list[str] = []
        self._default_product_type = "web"

        discovered_plugins, discovery_errors = discover_plugins(module_paths=module_paths, include_builtin=include_builtin)
        self._discovery_errors.extend(discovery_errors)
        for plugin in discovered_plugins:
            self.register_plugin(plugin)

    def register_plugin(self, plugin: AdapterPlugin) -> PluginInspection:
        if plugin.plugin_name in self._plugin_inspections:
            conflict = f"Duplicate plugin name '{plugin.plugin_name}' ignored."
            self._conflicts.append(conflict)
            existing = self._plugin_inspections[plugin.plugin_name]
            existing.validation.warnings.append(conflict)
            return existing

        validation: PluginValidationResult = validate_plugin(plugin)
        inspection = PluginInspection(plugin=plugin, validation=validation)
        self._plugin_inspections[plugin.plugin_name] = inspection

        if not validation.valid:
            return inspection

        for product_type in plugin.supported_product_types:
            if product_type in self._product_type_to_plugin:
                owner = self._product_type_to_plugin[product_type]
                message = (
                    f"Product type '{product_type}' already mapped to '{owner}'; "
                    f"plugin '{plugin.plugin_name}' kept as secondary."
                )
                self._conflicts.append(message)
                inspection.validation.warnings.append(message)
                self._plugins_by_product_type[product_type].append(plugin.plugin_name)
                continue

            self._product_type_to_plugin[product_type] = plugin.plugin_name
            self._plugins_by_product_type[product_type].append(plugin.plugin_name)

        return inspection

    def _resolve_plugin_name(self, product_type: str) -> tuple[str, str]:
        normalized = (product_type or "").lower().strip()
        plugin_name = self._product_type_to_plugin.get(normalized)
        if plugin_name:
            return plugin_name, "native"

        fallback_plugin = self._product_type_to_plugin.get(self._default_product_type)
        if fallback_plugin:
            return fallback_plugin, f"unsupported_product_type:{normalized or 'empty'}->web"
        raise ValueError("No plugin is registered for fallback product type 'web'.")

    def _resolve_inspection(self, product_type: str) -> tuple[PluginInspection, str]:
        plugin_name, fallback_mode = self._resolve_plugin_name(product_type)
        return self._plugin_inspections[plugin_name], fallback_mode

    def create_adapter(self, product_type: str, config: RuntimeConfig) -> BaseAdapter:
        inspection, _ = self._resolve_inspection(product_type)
        return inspection.plugin.adapter_class(config)

    def capability_names_for(self, product_type: str) -> list[str]:
        inspection, _ = self._resolve_inspection(product_type)
        return list(inspection.plugin.supported_capabilities)

    def fallback_mode_for(self, product_type: str) -> str:
        inspection, resolved_fallback = self._resolve_inspection(product_type)
        if resolved_fallback != "native":
            return resolved_fallback
        return inspection.plugin.fallback_mode

    def fallback_note_for(self, product_type: str) -> str | None:
        inspection, resolved_fallback = self._resolve_inspection(product_type)
        if resolved_fallback != "native":
            return (
                f"Product type '{product_type}' is unsupported; "
                f"fallback plugin '{inspection.plugin.plugin_name}' was used."
            )
        return inspection.validation.fallback_support_note

    def plugin_name_for(self, product_type: str) -> str:
        inspection, _ = self._resolve_inspection(product_type)
        return inspection.plugin.plugin_name

    def plugin_version_for(self, product_type: str) -> str:
        inspection, _ = self._resolve_inspection(product_type)
        return inspection.plugin.plugin_version

    def inspection_for_product_type(self, product_type: str) -> PluginInspection:
        inspection, _ = self._resolve_inspection(product_type)
        return inspection

    def inspect_plugin(self, plugin_name: str) -> PluginInspection | None:
        return self._plugin_inspections.get(plugin_name)

    def list_plugins(self, include_invalid: bool = True) -> list[PluginInspection]:
        plugins = list(self._plugin_inspections.values())
        if include_invalid:
            return sorted(plugins, key=lambda item: item.plugin.plugin_name)
        valid_plugins = [item for item in plugins if item.validation.valid]
        return sorted(valid_plugins, key=lambda item: item.plugin.plugin_name)

    def plugins_for_product_type(self, product_type: str) -> list[str]:
        normalized = (product_type or "").lower().strip()
        return list(self._plugins_by_product_type.get(normalized, []))

    def plugins_for_capability(self, capability: str) -> list[str]:
        normalized = (capability or "").strip()
        matches: list[str] = []
        for inspection in self.list_plugins(include_invalid=False):
            if normalized in inspection.plugin.supported_capabilities:
                matches.append(inspection.plugin.plugin_name)
        return sorted(matches)

    def capability_coverage_summary(self) -> dict[str, dict[str, Any]]:
        summary: dict[str, dict[str, Any]] = {}
        for inspection in self.list_plugins(include_invalid=False):
            for capability in inspection.plugin.supported_capabilities:
                if capability not in summary:
                    summary[capability] = {"plugin_count": 0, "plugins": []}
                summary[capability]["plugin_count"] += 1
                summary[capability]["plugins"].append(inspection.plugin.plugin_name)
        for capability in summary:
            summary[capability]["plugins"] = sorted(summary[capability]["plugins"])
        return dict(sorted(summary.items()))

    def supported_product_types(self) -> list[str]:
        return sorted(self._product_type_to_plugin.keys())

    def conflicts(self) -> list[str]:
        return list(self._conflicts)

    def discovery_errors(self) -> list[str]:
        return list(self._discovery_errors)


_DEFAULT_REGISTRY: PluginAwareRegistry | None = None


def get_registry(*, force_reload: bool = False, module_paths: list[str] | None = None) -> PluginAwareRegistry:
    global _DEFAULT_REGISTRY
    if force_reload or _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = PluginAwareRegistry(module_paths=module_paths, include_builtin=True)
    return _DEFAULT_REGISTRY


def build_default_registry() -> PluginAwareRegistry:
    return get_registry(force_reload=True)
