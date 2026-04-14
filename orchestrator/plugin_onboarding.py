from __future__ import annotations

from pathlib import Path
from typing import Any

from orchestrator.capabilities import CORE_CAPABILITIES, capability_names
from orchestrator.models import PluginOnboardingResult
from orchestrator.plugins import AdapterPlugin, PluginInspection
from orchestrator.taxonomy import supported_taxonomy_product_types

REQUIRED_ADAPTER_METHODS: tuple[str, ...] = ("discover", "plan", "generate_assets", "execute", "collect_evidence")

SAMPLE_MANIFEST_BY_PRODUCT: dict[str, str] = {
    "web": "manifests/samples/web_booking.yaml",
    "api": "manifests/samples/api_verify_store.yaml",
    "model": "manifests/samples/model_basalt.yaml",
    "mobile": "manifests/samples/mobile_app_smoke.yaml",
    "llm_app": "manifests/samples/llm_app_eval.yaml",
    "rag_app": "manifests/samples/rag_app_eval.yaml",
    "workflow": "manifests/samples/workflow_smoke.yaml",
    "data_pipeline": "manifests/samples/data_pipeline_validation.yaml",
}


def evaluate_plugin_onboarding(
    inspection: PluginInspection,
    project_root: str | Path = ".",
) -> PluginOnboardingResult:
    plugin = inspection.plugin
    validation = inspection.validation
    root = Path(project_root)

    checks_total = 6
    checks_passed = 0
    missing_items: list[str] = []
    notes: list[str] = []

    metadata_ok = bool(
        plugin.plugin_name
        and plugin.plugin_version
        and plugin.author
        and plugin.supported_product_types
        and isinstance(plugin.dependencies, list)
        and isinstance(plugin.compatibility, dict)
        and str(plugin.compatibility.get("python", "")).strip()
    )
    if metadata_ok:
        checks_passed += 1
    else:
        missing_items.append("plugin metadata completeness")

    capabilities_ok = validation.capability_completeness >= 1.0
    if capabilities_ok:
        checks_passed += 1
    else:
        missing_items.append("declared capabilities completeness")

    supported_taxonomy = set(supported_taxonomy_product_types())
    taxonomy_ok = all(item in supported_taxonomy for item in plugin.supported_product_types)
    if taxonomy_ok:
        checks_passed += 1
    else:
        missing_items.append("taxonomy mapping present")

    adapter_methods_ok = set(REQUIRED_ADAPTER_METHODS).issubset(set(validation.adapter_method_coverage))
    if adapter_methods_ok:
        checks_passed += 1
    else:
        missing_items.append("adapter interface completeness")

    sample_manifest_ok = True
    for product_type in plugin.supported_product_types:
        manifest_path = SAMPLE_MANIFEST_BY_PRODUCT.get(product_type, f"manifests/samples/{product_type}_sample.yaml")
        if not (root / manifest_path).exists():
            sample_manifest_ok = False
            break
    if sample_manifest_ok:
        checks_passed += 1
    else:
        missing_items.append("manifest sample exists")

    basic_test_ok = False
    plugin_slug = plugin.plugin_name.replace("-", "_")
    tests_dir = root / "tests"
    for candidate in tests_dir.glob("test_*.py"):
        if plugin_slug in candidate.name:
            basic_test_ok = True
            break
    if not basic_test_ok and plugin.health_metadata.get("test_placeholder"):
        basic_test_ok = True
        notes.append("Test placeholder declared in plugin metadata.")
    if basic_test_ok:
        checks_passed += 1
    else:
        missing_items.append("basic test coverage or placeholder")

    completeness_score = round(checks_passed / checks_total, 4)

    onboarding_status = "partial"
    if completeness_score >= 0.95 and validation.valid:
        onboarding_status = "ready"
    elif completeness_score < 0.5:
        onboarding_status = "not_ready"

    notes.append(f"Support level: {validation.support_level}")
    if validation.fallback_support_note:
        notes.append(validation.fallback_support_note)
    if validation.missing_recommended_capabilities:
        notes.append(
            f"Missing recommended capabilities: {', '.join(validation.missing_recommended_capabilities)}"
        )

    return PluginOnboardingResult(
        plugin_name=plugin.plugin_name,
        onboarding_status=onboarding_status,
        completeness_score=completeness_score,
        missing_items=missing_items,
        notes=notes,
    )


def evaluate_registry_onboarding(inspections: list[PluginInspection], project_root: str | Path = ".") -> list[PluginOnboardingResult]:
    return [evaluate_plugin_onboarding(inspection, project_root=project_root) for inspection in inspections]


def _class_name(product_type: str) -> str:
    return "".join(part.capitalize() for part in product_type.split("_"))


def _manifest_template(product_type: str, mode: str) -> str:
    if mode == "llm_like":
        return f"""project:
  name: {product_type}-sample
  type: {product_type}
interfaces:
  - name: chat
entry_points:
  - name: api
    target: /ask
artifacts:
  - name: {product_type}-dataset
    type: dataset
    path: manifests/samples/{product_type}_dataset.json
environment:
  stage: local
auth:
  required: false
request:
  goal: Smoke-check {product_type} behavior
  eval_cases:
    - prompt: "health check"
      expected_contains: "ok"
acceptance:
  max_failed: 0
  minimum_coverage: 0.5
outputs:
  report_format: json
oracle: {{}}
baseline: {{}}
dependencies: []
dimensions: []
"""
    if mode == "pipeline_like":
        return f"""project:
  name: {product_type}-sample
  type: {product_type}
interfaces: []
entry_points: []
artifacts:
  - name: {product_type}-schema
    type: schema
    path: manifests/samples/{product_type}_schema.json
environment:
  stage: local
auth:
  required: false
request:
  goal: Smoke-check {product_type} contract
  expected_columns:
    - id
acceptance:
  max_failed: 0
  minimum_coverage: 0.5
outputs:
  report_format: json
oracle: {{}}
baseline: {{}}
dependencies: []
dimensions: []
"""
    return f"""project:
  name: {product_type}-sample
  type: {product_type}
interfaces: []
entry_points: []
artifacts: []
environment:
  stage: local
auth:
  required: false
request:
  goal: Smoke-check {product_type}
acceptance:
  max_failed: 0
  minimum_coverage: 0.5
outputs:
  report_format: json
oracle: {{}}
baseline: {{}}
dependencies: []
dimensions: []
"""


def scaffold_plugin(
    product_type: str,
    mode: str = "generic",
    project_root: str | Path = ".",
) -> dict[str, Any]:
    normalized = product_type.lower().strip()
    safe_mode = mode if mode in {"generic", "llm_like", "pipeline_like"} else "generic"
    root = Path(project_root)

    adapter_path = root / "adapters" / f"{normalized}_adapter.py"
    runner_path = root / "runners" / f"{normalized}_runner.py"
    manifest_path = root / "manifests" / "samples" / f"{normalized}_sample.yaml"
    test_path = root / "tests" / f"test_{normalized}_plugin.py"

    class_name = f"{_class_name(normalized)}Adapter"
    runner_fn = f"run_{normalized}_smoke"

    adapter_template = f"""from __future__ import annotations

from adapters.base import BaseAdapter
from orchestrator.models import AdapterPlan, DiscoveryResult, EvidenceBundle, ExecutionResult, GeneratedAssets, NormalizedIntake, StrategyPlan
from runners.{normalized}_runner import {runner_fn}


class {class_name}(BaseAdapter):
    name = "{normalized}"

    def discover(self, intake: NormalizedIntake) -> DiscoveryResult:
        return DiscoveryResult(items=[intake.name], metadata={{"adapter": self.name}})

    def plan(self, intake: NormalizedIntake, strategy: StrategyPlan) -> AdapterPlan:
        return AdapterPlan(steps=["define checks"], coverage=strategy.coverage, metadata={{}})

    def generate_assets(self, intake: NormalizedIntake, adapter_plan: AdapterPlan) -> GeneratedAssets:
        return GeneratedAssets(artifacts=["{normalized}-smoke-skeleton"], metadata={{"step_count": len(adapter_plan.steps)}})

    def execute(self, intake: NormalizedIntake, generated_assets: GeneratedAssets) -> ExecutionResult:
        runner_result = {runner_fn}(evidence_dir=self.config.paths.evidence_dir)
        return ExecutionResult(
            status=runner_result.get("status", "blocked"),
            summary=runner_result.get("summary", {{}}),
            coverage=runner_result.get("coverage", {{}}),
            defect_details=runner_result.get("defects", []),
            evidence=runner_result.get("evidence", {{}}),
            recommendation_notes=runner_result.get("recommendation_notes", []),
            raw_output=runner_result.get("raw_output", {{}}),
        )

    def collect_evidence(self, intake: NormalizedIntake, execution_result: ExecutionResult) -> EvidenceBundle:
        evidence = execution_result.evidence.model_copy(deep=True)
        evidence.logs.append(f"Adapter={{self.name}}; status={{execution_result.status}}; scaffold=true")
        return evidence
"""

    runner_template = f"""from __future__ import annotations

from pathlib import Path


def {runner_fn}(evidence_dir: str) -> dict:
    logs = ["Scaffold runner executed in deterministic mode."]
    trace_file = Path(evidence_dir) / "{normalized}_smoke_trace.log"
    trace_file.parent.mkdir(parents=True, exist_ok=True)
    trace_file.write_text("\\n".join(logs), encoding="utf-8")
    return {{
        "status": "passed",
        "summary": {{"total_checks": 1, "passed": 1, "failed": 0, "blocked": 0, "skipped": 0}},
        "coverage": {{"planned_cases": 1, "executed_cases": 1, "execution_rate": 1.0, "requirement_coverage": 1.0}},
        "defects": [],
        "evidence": {{"logs": logs, "screenshots": [], "traces": [str(trace_file)], "artifacts": [str(trace_file)]}},
        "recommendation_notes": ["Replace scaffold runner logic with product-specific checks."],
        "raw_output": {{"scaffold": True}},
    }}
"""

    test_template = f"""from orchestrator.registry import get_registry


def test_{normalized}_plugin_placeholder() -> None:
    registry = get_registry()
    # Replace with concrete plugin tests after registration.
    assert isinstance(registry.plugins_for_capability("reporting"), list)
"""

    writes = {
        adapter_path: adapter_template,
        runner_path: runner_template,
        manifest_path: _manifest_template(normalized, safe_mode),
        test_path: test_template,
    }

    created_files: list[str] = []
    skipped_files: list[str] = []
    for path, contents in writes.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            skipped_files.append(str(path))
            continue
        path.write_text(contents, encoding="utf-8")
        created_files.append(str(path))

    return {
        "product_type": normalized,
        "mode": safe_mode,
        "created_files": created_files,
        "skipped_files": skipped_files,
        "capability_template": capability_names(CORE_CAPABILITIES),
    }
