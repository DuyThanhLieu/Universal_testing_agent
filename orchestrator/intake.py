from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from orchestrator.models import IntakeManifest, NormalizedIntake

REQUIRED_SECTIONS: tuple[str, ...] = (
    "artifacts",
    "environment",
    "request",
    "acceptance",
    "outputs",
)


def _normalize_manifest_shape(raw: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(raw)
    project = normalized.get("project")
    if isinstance(project, dict):
        if "name" not in normalized:
            normalized["name"] = project.get("name", "unnamed-project")
        if "project_type" not in normalized:
            normalized["project_type"] = project.get("type", "auto")
        if "project_subtype" not in normalized and project.get("subtype"):
            normalized["project_subtype"] = project.get("subtype")

    normalized.setdefault("name", "unnamed-project")
    normalized.setdefault("project_type", "auto")
    normalized.setdefault("project_subtype", None)
    normalized.setdefault("artifacts", [])
    normalized.setdefault("interfaces", [])
    normalized.setdefault("entry_points", [])
    normalized.setdefault("environment", {})
    normalized.setdefault("request", {})
    normalized.setdefault("acceptance", {})
    normalized.setdefault("outputs", {})
    normalized.setdefault("auth", {})
    normalized.setdefault("oracle", {})
    normalized.setdefault("baseline", {})
    normalized.setdefault("dependencies", [])
    normalized.setdefault("dimensions", [])
    normalized.setdefault("constraints", [])
    normalized.setdefault("api", {})
    normalized.setdefault("model", {})
    normalized.setdefault("labels", [])

    environment = normalized.get("environment", {})
    if isinstance(environment, dict):
        if not normalized.get("auth") and isinstance(environment.get("auth"), dict):
            normalized["auth"] = environment.get("auth", {})
        if not normalized.get("url"):
            candidate_url = environment.get("base_url")
            if candidate_url:
                normalized["url"] = candidate_url

    entry_points = normalized.get("entry_points", [])
    if not normalized.get("url") and isinstance(entry_points, list):
        for entry in entry_points:
            if isinstance(entry, dict):
                candidate = entry.get("url") or entry.get("base_url") or entry.get("target")
                if candidate:
                    normalized["url"] = candidate
                    break

    if not normalized.get("feature"):
        request = normalized.get("request", {})
        if isinstance(request, dict):
            normalized["feature"] = request.get("feature")

    return normalized


def load_manifest(manifest_path: str | Path) -> IntakeManifest:
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Manifest must be a YAML object")

    missing = [field for field in REQUIRED_SECTIONS if field not in raw]
    if missing:
        raise ValueError(f"Manifest missing required sections: {', '.join(missing)}")

    project = raw.get("project")
    has_legacy_project_type = "project_type" in raw
    has_v2_project_type = isinstance(project, dict) and bool(project.get("type"))
    if not has_legacy_project_type and not has_v2_project_type:
        raise ValueError("Manifest missing project type. Provide project_type or project.type")

    return IntakeManifest.model_validate(_normalize_manifest_shape(raw))


def normalize_input(manifest: IntakeManifest, manifest_path: str | Path) -> NormalizedIntake:
    first_entry_point = manifest.entry_points[0] if manifest.entry_points else {}
    first_entry_target = None
    if isinstance(first_entry_point, dict):
        first_entry_target = first_entry_point.get("url") or first_entry_point.get("base_url") or first_entry_point.get(
            "target"
        )

    target = (
        manifest.url
        or first_entry_target
        or manifest.environment.get("base_url")
        or manifest.request.get("target")
        or manifest.api.get("base_url")
        or manifest.model.get("endpoint")
    )

    return NormalizedIntake(
        manifest_path=str(Path(manifest_path)),
        name=manifest.name,
        project_type=manifest.project_type,
        project_subtype=manifest.project_subtype,
        url=manifest.url,
        target=target,
        feature=manifest.feature,
        labels=manifest.labels,
        artifacts=manifest.artifacts,
        interfaces=manifest.interfaces,
        entry_points=manifest.entry_points,
        environment=manifest.environment,
        request=manifest.request,
        acceptance=manifest.acceptance,
        outputs=manifest.outputs,
        oracle=manifest.oracle,
        baseline=manifest.baseline,
        dependencies=manifest.dependencies,
        dimensions=manifest.dimensions,
        auth=manifest.auth,
        constraints=manifest.constraints,
        api=manifest.api,
        model=manifest.model,
    )


def load_and_normalize(manifest_path: str | Path) -> NormalizedIntake:
    manifest = load_manifest(manifest_path)
    return normalize_input(manifest, manifest_path)
