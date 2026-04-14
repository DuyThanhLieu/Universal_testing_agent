from __future__ import annotations

from typing import Any

from adapters.base import BaseAdapter
from orchestrator.config import RuntimeConfig
from orchestrator.registry import get_registry


def select_adapter(product_type: str, config: RuntimeConfig) -> BaseAdapter:
    return get_registry().create_adapter(product_type, config)


def adapter_capabilities(product_type: str) -> list[str]:
    return get_registry().capability_names_for(product_type)


def adapter_fallback_mode(product_type: str) -> str:
    return get_registry().fallback_mode_for(product_type)


def adapter_fallback_note(product_type: str) -> str | None:
    return get_registry().fallback_note_for(product_type)


def adapter_plugin_name(product_type: str) -> str:
    return get_registry().plugin_name_for(product_type)


def adapter_plugin_version(product_type: str) -> str:
    return get_registry().plugin_version_for(product_type)


def adapter_plugin_inspection(product_type: str) -> dict[str, Any]:
    inspection = get_registry().inspection_for_product_type(product_type)
    return {
        "plugin_name": inspection.plugin.plugin_name,
        "plugin_version": inspection.plugin.plugin_version,
        "author": inspection.plugin.author,
        "dependencies": inspection.plugin.dependencies,
        "compatibility": inspection.plugin.compatibility,
        "supported_product_types": inspection.plugin.supported_product_types,
        "supported_capabilities": inspection.plugin.supported_capabilities,
        "fallback_mode": inspection.plugin.fallback_mode,
        "adapter_target": inspection.plugin.adapter_target(),
        "validation": inspection.validation.model_dump(mode="json"),
        "health_metadata": inspection.plugin.health_metadata,
        "discovered_from": inspection.plugin.discovered_from,
    }
