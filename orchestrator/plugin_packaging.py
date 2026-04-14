from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from orchestrator.models import utc_now_iso
from orchestrator.registry import PluginAwareRegistry

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def _validate_package_payload(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    required_fields = {
        "plugin_name",
        "plugin_version",
        "author",
        "dependencies",
        "compatibility",
        "supported_product_types",
        "supported_capabilities",
        "fallback_mode",
        "adapter_target",
    }
    missing = sorted(required_fields - set(payload.keys()))
    if missing:
        errors.append(f"Missing required fields: {', '.join(missing)}")

    version = str(payload.get("plugin_version", ""))
    if version and not SEMVER_PATTERN.match(version):
        errors.append("plugin_version must follow semantic versioning (x.y.z).")

    if not str(payload.get("plugin_name", "")).strip():
        errors.append("plugin_name must not be empty.")
    if not str(payload.get("author", "")).strip():
        errors.append("author must not be empty.")
    if not isinstance(payload.get("dependencies", []), list):
        errors.append("dependencies must be a list.")
    compatibility = payload.get("compatibility", {})
    if not isinstance(compatibility, dict):
        errors.append("compatibility must be an object.")
    elif not str(compatibility.get("python", "")).strip():
        errors.append("compatibility.python must be provided.")
    if not isinstance(payload.get("supported_product_types", []), list):
        errors.append("supported_product_types must be a list.")
    if not isinstance(payload.get("supported_capabilities", []), list):
        errors.append("supported_capabilities must be a list.")

    return len(errors) == 0, errors


def export_plugin_package(
    registry: PluginAwareRegistry,
    plugin_name: str,
    output_path: str | Path,
) -> tuple[Path, dict[str, Any]]:
    inspection = registry.inspect_plugin(plugin_name)
    if inspection is None:
        raise ValueError(f"Plugin '{plugin_name}' not found.")

    package_payload: dict[str, Any] = {
        "plugin_name": inspection.plugin.plugin_name,
        "plugin_version": inspection.plugin.plugin_version,
        "author": inspection.plugin.author,
        "dependencies": inspection.plugin.dependencies,
        "compatibility": inspection.plugin.compatibility,
        "supported_product_types": inspection.plugin.supported_product_types,
        "supported_capabilities": inspection.plugin.supported_capabilities,
        "fallback_mode": inspection.plugin.fallback_mode,
        "adapter_target": inspection.plugin.adapter_target(),
        "health_metadata": inspection.plugin.health_metadata,
        "discovered_from": inspection.plugin.discovered_from,
        "validation": inspection.validation.model_dump(mode="json"),
        "exported_at": utc_now_iso(),
    }

    valid, errors = _validate_package_payload(package_payload)
    if not valid:
        raise ValueError("; ".join(errors))

    output = Path(output_path)
    if output.suffix.lower() != ".json":
        output = output / f"{inspection.plugin.plugin_name}-{inspection.plugin.plugin_version}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(package_payload, indent=2), encoding="utf-8")
    return output, package_payload


def import_plugin_package(
    package_path: str | Path,
    import_dir: str | Path,
) -> tuple[Path, dict[str, Any], list[str]]:
    source = Path(package_path)
    if not source.exists():
        raise FileNotFoundError(f"Plugin package not found: {source}")

    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Plugin package payload must be a JSON object.")

    valid, errors = _validate_package_payload(payload)
    package_name = str(payload.get("plugin_name", "unknown")).strip() or "unknown"
    package_version = str(payload.get("plugin_version", "0.0.0")).strip() or "0.0.0"

    target = Path(import_dir) / f"{package_name}-{package_version}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload["imported_at"] = utc_now_iso()
    payload["source_package"] = str(source)
    payload["import_valid"] = valid
    payload["import_errors"] = errors
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return target, payload, errors
