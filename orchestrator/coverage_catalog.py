from __future__ import annotations

import json
from pathlib import Path

from orchestrator.models import CoverageCatalogEntry, CoverageCatalogSummary, utc_now_iso
from orchestrator.plugin_onboarding import evaluate_registry_onboarding
from orchestrator.registry import PluginAwareRegistry


def build_coverage_catalog(registry: PluginAwareRegistry, project_root: str | Path = ".") -> CoverageCatalogSummary:
    inspections = registry.list_plugins(include_invalid=True)
    onboarding_results = {item.plugin_name: item for item in evaluate_registry_onboarding(inspections, project_root=project_root)}

    entries: list[CoverageCatalogEntry] = []
    for inspection in inspections:
        onboarding = onboarding_results.get(inspection.plugin.plugin_name)
        entries.append(
            CoverageCatalogEntry(
                plugin_name=inspection.plugin.plugin_name,
                plugin_version=inspection.plugin.plugin_version,
                author=inspection.plugin.author,
                dependencies=inspection.plugin.dependencies,
                compatibility=inspection.plugin.compatibility,
                product_types=inspection.plugin.supported_product_types,
                capabilities=inspection.plugin.supported_capabilities,
                support_level=inspection.validation.support_level,
                fallback_mode=inspection.plugin.fallback_mode,
                fallback_note=inspection.validation.fallback_support_note,
                missing_recommended_capabilities=inspection.validation.missing_recommended_capabilities,
                onboarding_status=onboarding.onboarding_status if onboarding else "partial",
            )
        )
    entries.sort(key=lambda item: item.plugin_name)
    return CoverageCatalogSummary(generated_at=utc_now_iso(), entries=entries)


def render_coverage_catalog_markdown(catalog: CoverageCatalogSummary) -> str:
    lines = [
        "# Coverage Catalog",
        "",
        f"- Generated At: `{catalog.generated_at}`",
        "",
        "| Plugin | Version | Author | Product Types | Support Level | Fallback | Missing Capabilities | Onboarding |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for entry in catalog.entries:
        lines.append(
            "| {plugin} | {version} | {author} | {types} | {support} | {fallback} | {missing} | {onboarding} |".format(
                plugin=entry.plugin_name,
                version=entry.plugin_version,
                author=entry.author or "unknown",
                types=", ".join(entry.product_types) or "(none)",
                support=entry.support_level,
                fallback=entry.fallback_mode,
                missing=", ".join(entry.missing_recommended_capabilities) or "(none)",
                onboarding=entry.onboarding_status,
            )
        )
    lines.append("")
    return "\n".join(lines)


def save_coverage_catalog(
    catalog: CoverageCatalogSummary,
    output_json: str | Path,
    output_md: str | Path,
) -> tuple[Path, Path]:
    json_path = Path(output_json)
    md_path = Path(output_md)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(catalog.model_dump(mode="json"), indent=2), encoding="utf-8")
    md_path.write_text(render_coverage_catalog_markdown(catalog), encoding="utf-8")
    return json_path, md_path
