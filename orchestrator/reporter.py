from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar
import xml.etree.ElementTree as ET

from pydantic import BaseModel

from orchestrator.config import RuntimeConfig, load_runtime_config
from orchestrator.history import load_history_records
from orchestrator.models import (
    ComparisonResult,
    ContractValidationResult,
    ExecutionEnvelope,
    PluginOnboardingResult,
    PluginReportContext,
    PluginValidationSummary,
    QualityGateResult,
    StandardReport,
    TrendAnalysis,
    utc_now_iso,
)
from orchestrator.policy import evaluate_release_policy
from orchestrator.quality_gates import evaluate_quality_gates
from orchestrator.trends import flaky_suspicion_from_history

TModel = TypeVar("TModel", bound=BaseModel)


def _load_optional_model(path: Path, model: type[TModel]) -> TModel | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return model.model_validate(payload)
    except Exception:
        return None


def _existing_artifact_references(envelope: ExecutionEnvelope, config: RuntimeConfig) -> list[str]:
    references = list(envelope.generated_artifacts)
    well_known = [
        Path(config.paths.latest_checklist_file),
        Path(config.paths.latest_checklist_markdown_file),
        Path(config.paths.latest_testcases_file),
        Path(config.paths.latest_testcases_markdown_file),
        Path(config.paths.latest_bug_report_template_file),
        Path(config.paths.latest_generated_assets_index_file),
        Path(config.paths.latest_junit_file),
        Path(config.paths.latest_ci_summary_file),
        Path(config.paths.latest_quality_gates_file),
        Path(config.paths.latest_trends_file),
        Path(config.paths.latest_contract_validation_file),
        Path(config.paths.latest_compare_file),
        Path(config.paths.latest_coverage_catalog_file),
        Path(config.paths.latest_coverage_catalog_markdown_file),
    ]
    for candidate in well_known:
        if candidate.exists():
            references.append(str(candidate))
    return list(dict.fromkeys(references))


def generate_report(envelope: ExecutionEnvelope, config: RuntimeConfig | None = None) -> StandardReport:
    runtime_config = config or load_runtime_config()
    acceptance = envelope.metadata.get("acceptance", {})
    policy = evaluate_release_policy(
        acceptance=acceptance if isinstance(acceptance, dict) else {},
        summary=envelope.summary,
        coverage=envelope.coverage,
        defects=envelope.defects,
    )

    trend_summary = _load_optional_model(Path(runtime_config.paths.latest_trends_file), TrendAnalysis)
    contract_summary = _load_optional_model(
        Path(runtime_config.paths.latest_contract_validation_file), ContractValidationResult
    )
    comparison_summary = _load_optional_model(Path(runtime_config.paths.latest_compare_file), ComparisonResult)
    if contract_summary is None:
        inline_contract = envelope.metadata.get("contract_validation_summary")
        if isinstance(inline_contract, dict) and inline_contract:
            try:
                contract_summary = ContractValidationResult.model_validate(inline_contract)
            except Exception:
                contract_summary = None

    recommendation_notes = list(envelope.recommendation.notes)
    recommendation_notes.extend(policy.reasons)
    recommendation_notes = list(dict.fromkeys(recommendation_notes))

    known_gaps = list(envelope.known_gaps)
    if envelope.summary.blocked > 0:
        known_gaps.append("Blocked checks reduce confidence for release decisions.")
    known_gaps = list(dict.fromkeys(known_gaps))

    assumptions = list(envelope.assumptions)
    assumptions.extend(
        [
            "Policy gate uses manifest acceptance rules when available.",
            "Generated assets are referenced when present in the results directory.",
        ]
    )
    assumptions = list(dict.fromkeys(assumptions))

    artifact_references = _existing_artifact_references(envelope, runtime_config)
    capabilities_used = [str(item) for item in envelope.metadata.get("capabilities_used", [])]
    capability_path_used = list(envelope.capability_path_used or capabilities_used)
    taxonomy_coverage_focus = [str(item) for item in envelope.metadata.get("taxonomy_coverage_focus", [])]
    fallback_execution_note = envelope.metadata.get("fallback_execution_note")
    if not isinstance(fallback_execution_note, str):
        fallback_execution_note = None

    plugin_context = envelope.plugin
    if plugin_context is None:
        raw_context = envelope.metadata.get("plugin_context")
        if isinstance(raw_context, dict):
            try:
                plugin_context = PluginReportContext.model_validate(
                    {
                        "plugin_name": raw_context.get("plugin_name", ""),
                        "plugin_version": raw_context.get("plugin_version", ""),
                        "author": raw_context.get("author"),
                        "dependencies": raw_context.get("dependencies", []),
                        "compatibility": raw_context.get("compatibility", {}),
                        "supported_product_types": raw_context.get("supported_product_types", []),
                        "supported_capabilities": raw_context.get("supported_capabilities", []),
                        "fallback_mode": raw_context.get("fallback_mode", "native"),
                        "adapter_target": raw_context.get("adapter_target", ""),
                        "health_metadata": raw_context.get("health_metadata", {}),
                        "discovered_from": raw_context.get("discovered_from", "unknown"),
                    }
                )
            except Exception:
                plugin_context = None

    plugin_validation = envelope.plugin_validation
    if plugin_validation is None:
        raw_plugin_context = envelope.metadata.get("plugin_context", {})
        raw_validation = raw_plugin_context.get("validation", {}) if isinstance(raw_plugin_context, dict) else {}
        if isinstance(raw_validation, dict) and raw_validation:
            try:
                plugin_validation = PluginValidationSummary.model_validate(raw_validation)
            except Exception:
                plugin_validation = None

    plugin_onboarding = envelope.plugin_onboarding
    if plugin_onboarding is None:
        raw_onboarding = envelope.metadata.get("plugin_onboarding")
        if isinstance(raw_onboarding, dict) and raw_onboarding:
            try:
                plugin_onboarding = PluginOnboardingResult.model_validate(raw_onboarding)
            except Exception:
                plugin_onboarding = None

    support_level = envelope.support_level
    if support_level is None and plugin_validation is not None:
        support_level = plugin_validation.support_level
    if support_level is None:
        support_level = envelope.metadata.get("support_level")
    if support_level is not None and not isinstance(support_level, str):
        support_level = str(support_level)

    coverage_catalog_reference = envelope.metadata.get("coverage_catalog_reference")
    if coverage_catalog_reference is not None and not isinstance(coverage_catalog_reference, str):
        coverage_catalog_reference = str(coverage_catalog_reference)

    quality_gates = envelope.quality_gates
    if quality_gates is None:
        fallback_mode = envelope.metadata.get("adapter_registry_fallback_mode", "native")
        if not isinstance(fallback_mode, str):
            fallback_mode = "native"
        quality_gates = evaluate_quality_gates(
            acceptance=acceptance if isinstance(acceptance, dict) else {},
            summary=envelope.summary,
            coverage=envelope.coverage,
            defects=envelope.defects,
            contract_validation=contract_summary,
            fallback_mode=fallback_mode,
        )
    if not isinstance(quality_gates, QualityGateResult):
        quality_gates = QualityGateResult.model_validate(quality_gates)

    regression_signals: list[str] = []
    if comparison_summary:
        regression_signals.extend(comparison_summary.regression_signals)
    if trend_summary and trend_summary.overall_direction == "degrading":
        regression_signals.append("Trend analysis indicates degrading overall direction.")
    regression_signals = list(dict.fromkeys(regression_signals))

    history_records = load_history_records(runtime_config.paths.history_dir)
    flaky_note = flaky_suspicion_from_history(history_records)
    if fallback_execution_note:
        known_gaps.append(fallback_execution_note)
        known_gaps = list(dict.fromkeys(known_gaps))

    capability_coverage_summary: dict[str, object] = {}
    if plugin_context is not None:
        for capability in plugin_context.supported_capabilities:
            capability_coverage_summary[capability] = {
                "supported": True,
                "used": capability in capability_path_used,
            }

    return StandardReport(
        run_id=envelope.run_id,
        project_name=envelope.project_name,
        project_type=envelope.project_type,
        adapter=envelope.adapter,
        status=envelope.status,
        started_at=envelope.started_at,
        finished_at=envelope.finished_at,
        duration_seconds=envelope.duration_seconds,
        summary=envelope.summary,
        coverage=envelope.coverage,
        defects=envelope.defects,
        defect_details=envelope.defect_details,
        evidence=envelope.evidence,
        recommendation={
            "release_ready": envelope.recommendation.release_ready and policy.release_ready and quality_gates.gate_status == "pass",
            "notes": recommendation_notes,
        },
        plugin=plugin_context,
        plugin_validation=plugin_validation,
        plugin_onboarding=plugin_onboarding,
        support_level=support_level,
        coverage_catalog_reference=coverage_catalog_reference,
        capability_path_used=capability_path_used,
        policy=policy,
        quality_gates=quality_gates,
        release_gate_summary=quality_gates.gate_status.upper(),
        known_gaps=known_gaps,
        assumptions=assumptions,
        artifact_references=artifact_references,
        run_metadata=envelope.run_metadata,
        capabilities_used=capabilities_used,
        capability_coverage_summary=capability_coverage_summary,
        taxonomy_coverage_focus=taxonomy_coverage_focus,
        fallback_execution_note=fallback_execution_note,
        trend_summary=trend_summary,
        contract_validation_summary=contract_summary,
        comparison_summary=comparison_summary,
        regression_signals=regression_signals,
        flaky_suspicion_note=flaky_note,
        generated_at=utc_now_iso(),
    )


def save_report(report: StandardReport, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8")
    return path


def _format_list(items: list[str]) -> str:
    if not items:
        return "- (none)"
    return "\n".join(f"- {item}" for item in items)


def render_markdown_report(report: StandardReport) -> str:
    plugin_section = "- (not available)"
    if report.plugin is not None:
        plugin_section = (
            f"- Plugin: `{report.plugin.plugin_name}`\n"
            f"- Version: `{report.plugin.plugin_version}`\n"
            f"- Author: `{report.plugin.author or 'unknown'}`\n"
            f"- Dependencies: {', '.join(report.plugin.dependencies) if report.plugin.dependencies else '(none)'}\n"
            f"- Compatibility: `{report.plugin.compatibility}`\n"
            f"- Adapter Target: `{report.plugin.adapter_target}`\n"
            f"- Fallback Mode: `{report.plugin.fallback_mode}`\n"
            f"- Discovered From: `{report.plugin.discovered_from}`"
        )

    plugin_validation_section = "- (not available)"
    if report.plugin_validation is not None:
        plugin_validation_section = (
            f"- Valid: `{report.plugin_validation.valid}`\n"
            f"- Capability Completeness: `{report.plugin_validation.capability_completeness}`\n"
            f"- Support Level: `{report.plugin_validation.support_level}`\n"
            f"- Adapter Method Coverage: {', '.join(report.plugin_validation.adapter_method_coverage) if report.plugin_validation.adapter_method_coverage else '(none)'}\n"
            f"- Missing Recommended Capabilities: {', '.join(report.plugin_validation.missing_recommended_capabilities) if report.plugin_validation.missing_recommended_capabilities else '(none)'}\n"
            f"- Warnings: {', '.join(report.plugin_validation.warnings) if report.plugin_validation.warnings else '(none)'}\n"
            f"- Errors: {', '.join(report.plugin_validation.errors) if report.plugin_validation.errors else '(none)'}"
        )

    onboarding_section = "- (not available)"
    if report.plugin_onboarding is not None:
        onboarding_section = (
            f"- Status: `{report.plugin_onboarding.onboarding_status}`\n"
            f"- Completeness Score: `{report.plugin_onboarding.completeness_score}`\n"
            f"- Missing Items: {', '.join(report.plugin_onboarding.missing_items) if report.plugin_onboarding.missing_items else '(none)'}\n"
            f"- Notes: {', '.join(report.plugin_onboarding.notes) if report.plugin_onboarding.notes else '(none)'}"
        )

    trend_section = "- (not available)"
    if report.trend_summary is not None:
        trend_section = (
            f"- Runs analyzed: `{report.trend_summary.runs_analyzed}`\n"
            f"- Overall direction: `{report.trend_summary.overall_direction}`\n"
            f"- Pass rate trend: `{report.trend_summary.pass_rate_trend}`\n"
            f"- Coverage trend: `{report.trend_summary.coverage_trend}`\n"
            f"- Defect trend: `{report.trend_summary.defect_trend}`\n"
            f"- Release readiness trend: `{report.trend_summary.release_readiness_trend}`"
        )

    contract_section = "- (not available)"
    if report.contract_validation_summary is not None:
        contract_section = (
            f"- Verdict: `{report.contract_validation_summary.verdict}`\n"
            f"- Release Ready: `{report.contract_validation_summary.release_ready}`\n"
            f"- Reasons: {', '.join(report.contract_validation_summary.reasons) if report.contract_validation_summary.reasons else '(none)'}"
        )

    comparison_section = "- (not available)"
    if report.comparison_summary is not None:
        comparison_section = (
            f"- Changed: `{report.comparison_summary.changed}`\n"
            f"- Passed delta: `{report.comparison_summary.passed_delta}`\n"
            f"- Failed delta: `{report.comparison_summary.failed_delta}`\n"
            f"- Coverage delta: `{report.comparison_summary.coverage_delta}`\n"
            f"- Defect delta: `{report.comparison_summary.defect_delta}`\n"
            f"- Release ready changed: `{report.comparison_summary.release_ready_changed}`"
        )

    quality_gate_section = "- (not available)"
    if report.quality_gates is not None:
        quality_gate_section = (
            f"- Gate Status: `{report.quality_gates.gate_status}`\n"
            f"- Recommendation: {report.quality_gates.recommendation}\n"
            f"- Reasons: {', '.join(report.quality_gates.gate_reasons) if report.quality_gates.gate_reasons else '(none)'}\n"
            f"- Blocking Issues: {', '.join(report.quality_gates.blocking_issues) if report.quality_gates.blocking_issues else '(none)'}"
        )

    return f"""# Universal Testing Agent Report

## Project Summary
- Run ID: `{report.run_id}`
- Project: `{report.project_name}`
- Project Type: `{report.project_type}`
- Adapter: `{report.adapter}`
- Status: `{report.status}`
- Started: `{report.started_at}`
- Finished: `{report.finished_at}`
- Duration (s): `{report.duration_seconds}`

## Execution Summary
- Total Checks: `{report.summary.total_checks}`
- Passed: `{report.summary.passed}`
- Failed: `{report.summary.failed}`
- Blocked: `{report.summary.blocked}`
- Skipped: `{report.summary.skipped}`
- Planned Cases: `{report.coverage.planned_cases}`
- Executed Cases: `{report.coverage.executed_cases}`
- Execution Rate: `{report.coverage.execution_rate}`
- Requirement Coverage: `{report.coverage.requirement_coverage}`

## Defects
- Blocker: `{report.defects.blocker}`
- Critical: `{report.defects.critical}`
- High: `{report.defects.high}`
- Medium: `{report.defects.medium}`
- Low: `{report.defects.low}`

## Defect Breakdown
{_format_list([f"{item.id} | severity={item.severity} | category={item.category} | reproducibility={item.reproducibility} | confidence={item.confidence_score}" for item in report.defect_details])}

## Evidence
### Logs
{_format_list(report.evidence.logs)}

### Screenshots
{_format_list(report.evidence.screenshots)}

### Traces
{_format_list(report.evidence.traces)}

### Artifacts
{_format_list(report.evidence.artifacts)}

## Release Recommendation
- Release Ready: `{report.recommendation.release_ready}`
### Notes
{_format_list(report.recommendation.notes)}

## Policy Evaluation
- Verdict: `{report.policy.verdict}`
- Release Ready: `{report.policy.release_ready}`
### Reasons
{_format_list(report.policy.reasons)}

## Quality Gates
{quality_gate_section}

## Release Gate Summary
- Gate: `{report.release_gate_summary}`

## Capabilities Used
{_format_list(report.capabilities_used)}

## Capability Coverage Summary
{_format_list([f"{key}: used={value.get('used')} supported={value.get('supported')}" for key, value in report.capability_coverage_summary.items()])}

## Capability Path Used
{_format_list(report.capability_path_used)}

## Plugin Context
{plugin_section}

## Plugin Validation
{plugin_validation_section}

## Plugin Onboarding
{onboarding_section}

## Support Level
- {report.support_level or "(none)"}

## Coverage Catalog Reference
- {report.coverage_catalog_reference or "(none)"}

## Taxonomy Coverage Focus
{_format_list(report.taxonomy_coverage_focus)}

## Fallback Execution Note
- {report.fallback_execution_note or "(none)"}

## Trend Summary
{trend_section}

## Contract Validation Summary
{contract_section}

## Comparison Summary
{comparison_section}

## Regression Signals
{_format_list(report.regression_signals)}

## Flaky Suspicion
- {report.flaky_suspicion_note or "(none)"}

## Known Gaps
{_format_list(report.known_gaps)}

## Assumptions
{_format_list(report.assumptions)}

## Generated Artifact References
{_format_list(report.artifact_references)}
"""


def save_markdown_report(report: StandardReport, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown_report(report), encoding="utf-8")
    return path


def render_junit_xml(report: StandardReport) -> str:
    total = max(report.summary.total_checks, 1)
    failures = max(report.summary.failed, 0)
    errors = max(report.summary.blocked, 0)
    skipped = max(report.summary.skipped, 0)
    if report.quality_gates and report.quality_gates.gate_status == "fail":
        failures += 1
    elif report.quality_gates and report.quality_gates.gate_status == "warning":
        skipped += 1
    total += 1  # reserve one testcase for quality gate
    passed = max(total - failures - errors - skipped, 0)

    suite = ET.Element(
        "testsuite",
        attrib={
            "name": f"uta.{report.project_type}",
            "tests": str(total),
            "failures": str(failures),
            "errors": str(errors),
            "skipped": str(skipped),
            "time": str(report.duration_seconds),
        },
    )

    for index in range(1, passed + 1):
        ET.SubElement(
            suite,
            "testcase",
            attrib={"classname": report.adapter, "name": f"check.pass.{index}", "time": "0"},
        )

    for index in range(1, failures + 1):
        case = ET.SubElement(
            suite,
            "testcase",
            attrib={"classname": report.adapter, "name": f"check.fail.{index}", "time": "0"},
        )
        failure = ET.SubElement(case, "failure", attrib={"message": "failed quality/assertion check"})
        failure.text = "UTA execution reported a failed check."

    for index in range(1, errors + 1):
        case = ET.SubElement(
            suite,
            "testcase",
            attrib={"classname": report.adapter, "name": f"check.blocked.{index}", "time": "0"},
        )
        error = ET.SubElement(case, "error", attrib={"message": "blocked execution check"})
        error.text = "UTA execution reported a blocked check."

    for index in range(1, skipped + 1):
        case = ET.SubElement(
            suite,
            "testcase",
            attrib={"classname": report.adapter, "name": f"check.skipped.{index}", "time": "0"},
        )
        ET.SubElement(case, "skipped")

    quality_case = ET.SubElement(
        suite,
        "testcase",
        attrib={"classname": "quality_gates", "name": "release_gate", "time": "0"},
    )
    if report.quality_gates and report.quality_gates.gate_status == "fail":
        failure = ET.SubElement(quality_case, "failure", attrib={"message": "quality gate failed"})
        failure.text = "; ".join(report.quality_gates.blocking_issues or report.quality_gates.gate_reasons)
    elif report.quality_gates and report.quality_gates.gate_status == "warning":
        skipped_node = ET.SubElement(quality_case, "skipped", attrib={"message": "quality gate warning"})
        skipped_node.text = "; ".join(report.quality_gates.gate_reasons)

    return ET.tostring(suite, encoding="unicode")


def save_junit_report(report: StandardReport, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_junit_xml(report), encoding="utf-8")
    return path


def build_ci_summary(report: StandardReport) -> dict[str, object]:
    gate_status = report.quality_gates.gate_status if report.quality_gates else "warning"
    return {
        "run_id": report.run_id,
        "project_name": report.project_name,
        "project_type": report.project_type,
        "status": report.status,
        "gate_status": gate_status,
        "release_ready": report.recommendation.release_ready,
        "summary": report.summary.model_dump(mode="json"),
        "coverage": report.coverage.model_dump(mode="json"),
        "defects": report.defects.model_dump(mode="json"),
        "plugin": report.plugin.model_dump(mode="json") if report.plugin else None,
        "support_level": report.support_level,
        "fallback_execution_note": report.fallback_execution_note,
        "generated_at": report.generated_at,
    }


def save_ci_summary(report: StandardReport, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_ci_summary(report)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
