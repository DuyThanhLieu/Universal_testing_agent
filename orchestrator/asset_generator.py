from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from orchestrator.config import RuntimeConfig
from orchestrator.models import NormalizedIntake, StrategyPlan


class GeneratedAssetBundle(BaseModel):
    project_type: str
    checklist: list[dict[str, Any]] = Field(default_factory=list)
    testcases: list[dict[str, Any]] = Field(default_factory=list)
    known_gaps: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    artifact_paths: list[str] = Field(default_factory=list)


def _web_assets(intake: NormalizedIntake, strategy: StrategyPlan) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    checklist = [
        {"id": "WEB-CHK-001", "item": "Target URL is configured", "priority": "P0"},
        {"id": "WEB-CHK-002", "item": "Auth expectation is defined", "priority": "P1"},
        {"id": "WEB-CHK-003", "item": "Feature route is reachable", "priority": "P1"},
    ]
    testcases = [
        {
            "id": "WEB-TC-001",
            "title": "Open primary web target",
            "type": "smoke",
            "steps": [f"Navigate to {intake.target or intake.url or '[target]'}", "Capture status and page evidence"],
            "expected": "Status below 400 and evidence traces generated",
        },
        {
            "id": "WEB-TC-002",
            "title": f"Validate feature workflow ({intake.feature or 'primary'})",
            "type": "functional",
            "steps": ["Open feature entry route", "Verify minimal flow interactions"],
            "expected": "No blocking issues in core workflow",
        },
    ]
    known_gaps = ["No deep browser interaction assertions in smoke-generated assets."]
    assumptions = [f"Strategy priorities used: {', '.join(strategy.execution_priorities) or 'default'}"]
    return checklist, testcases, known_gaps, assumptions


def _api_assets(intake: NormalizedIntake, strategy: StrategyPlan) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    endpoints = intake.request.get("endpoints", ["/"])
    checklist = [
        {"id": "API-CHK-001", "item": "Base URL or simulation mode defined", "priority": "P0"},
        {"id": "API-CHK-002", "item": "OpenAPI/Swagger artifact available", "priority": "P0"},
        {"id": "API-CHK-003", "item": "Negative status code checks included", "priority": "P1"},
    ]
    testcases = [
        {
            "id": f"API-TC-{idx+1:03d}",
            "title": f"Smoke GET {endpoint}",
            "type": "contract-smoke",
            "steps": [
                f"Send GET request to {endpoint}",
                "Verify status code and basic payload structure",
            ],
            "expected": "No 5xx responses and payload shape not empty",
        }
        for idx, endpoint in enumerate(endpoints)
    ]
    known_gaps = ["Payload schema diff checks are not auto-generated in v1.3."]
    assumptions = [f"Endpoint matrix size: {len(strategy.endpoint_matrix_summary)}"]
    return checklist, testcases, known_gaps, assumptions


def _model_assets(intake: NormalizedIntake, strategy: StrategyPlan) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    checklist = [
        {"id": "MOD-CHK-001", "item": "Labels are available for evaluation", "priority": "P0"},
        {"id": "MOD-CHK-002", "item": "Dataset metadata/sample references exist", "priority": "P0"},
        {"id": "MOD-CHK-003", "item": "Quality threshold is defined", "priority": "P1"},
    ]
    testcases = [
        {
            "id": "MOD-TC-001",
            "title": "Compute metadata quality proxy metrics",
            "type": "offline-eval",
            "steps": ["Count labels", "Count dataset samples", "Compute quality score proxy"],
            "expected": "Metrics available for policy gating",
        },
        {
            "id": "MOD-TC-002",
            "title": "Optional endpoint smoke evaluation",
            "type": "online-smoke",
            "steps": ["Invoke model endpoint if configured", "Validate expected token in response"],
            "expected": "No blocking endpoint errors for configured live checks",
        },
    ]
    known_gaps = ["Task-specific benchmark scoring is not generated automatically."]
    assumptions = [f"Evaluation dimensions: {', '.join(strategy.evaluation_dimensions) or 'default'}"]
    return checklist, testcases, known_gaps, assumptions


def _mobile_assets(intake: NormalizedIntake, strategy: StrategyPlan) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    checklist = [
        {"id": "MOB-CHK-001", "item": "App identifier or package artifact is configured", "priority": "P0"},
        {"id": "MOB-CHK-002", "item": "Entry points/navigation targets are defined", "priority": "P0"},
        {"id": "MOB-CHK-003", "item": "Permissions and auth expectations are declared", "priority": "P1"},
        {"id": "MOB-CHK-004", "item": "Basic crash/usability smoke checks are included", "priority": "P1"},
    ]
    testcases = [
        {
            "id": "MOB-TC-001",
            "title": "Install/open flow smoke",
            "type": "mobile-smoke",
            "steps": ["Resolve app package or app_id", "Launch app in skeleton mode", "Capture startup trace evidence"],
            "expected": "No blocking launch/configuration errors in smoke mode",
        },
        {
            "id": "MOB-TC-002",
            "title": "Navigation + permission gate checks",
            "type": "mobile-usability",
            "steps": ["Open configured entry points", "Validate permission prompts configuration", "Record auth gate expectation"],
            "expected": "Critical navigation and permission assumptions are satisfied",
        },
    ]
    known_gaps = ["Gesture-level interaction and device-farm execution are not auto-generated in v1.5."]
    assumptions = [f"Coverage focus: {', '.join(strategy.coverage_focus) or 'mobile smoke defaults'}"]
    return checklist, testcases, known_gaps, assumptions


def _llm_app_assets(intake: NormalizedIntake, strategy: StrategyPlan) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    checklist = [
        {"id": "LLM-CHK-001", "item": "Prompt/eval case set is configured", "priority": "P0"},
        {"id": "LLM-CHK-002", "item": "Safety and fallback strategy are declared", "priority": "P0"},
        {"id": "LLM-CHK-003", "item": "Tool-use readiness signals are available", "priority": "P1"},
        {"id": "LLM-CHK-004", "item": "Response consistency checks are defined", "priority": "P1"},
    ]
    testcases = [
        {
            "id": "LLM-TC-001",
            "title": "Prompt-response quality smoke",
            "type": "llm-quality",
            "steps": ["Run deterministic eval cases", "Check expected token signals", "Capture response logs"],
            "expected": "Expected output signals are detected for critical prompts",
        },
        {
            "id": "LLM-TC-002",
            "title": "Safety/tool/fallback readiness",
            "type": "llm-safety",
            "steps": ["Validate safety indicators", "Validate tool declarations", "Validate fallback strategy"],
            "expected": "No blocking gaps in safety/tool/fallback baseline",
        },
    ]
    known_gaps = ["Judge-model scoring and red-team coverage are not auto-generated in v1.5 skeleton mode."]
    assumptions = [f"Capability expectations: {', '.join(strategy.capability_expectations) or 'llm_app defaults'}"]
    return checklist, testcases, known_gaps, assumptions


def _rag_app_assets(intake: NormalizedIntake, strategy: StrategyPlan) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    checklist = [
        {"id": "RAG-CHK-001", "item": "Retrieval corpus is configured", "priority": "P0"},
        {"id": "RAG-CHK-002", "item": "Citation expectation policy is defined", "priority": "P0"},
        {"id": "RAG-CHK-003", "item": "Grounding/hallucination checks are configured", "priority": "P1"},
        {"id": "RAG-CHK-004", "item": "Context/tool fallback strategy is declared", "priority": "P1"},
    ]
    testcases = [
        {
            "id": "RAG-TC-001",
            "title": "Retrieval-grounded response smoke",
            "type": "rag-grounding",
            "steps": ["Execute eval prompts", "Verify expected answer token", "Verify context grounding signal"],
            "expected": "Responses remain grounded to retrieval context",
        },
        {
            "id": "RAG-TC-002",
            "title": "Citation and fallback policy checks",
            "type": "rag-citation",
            "steps": ["Validate citation token expectations", "Validate fallback behavior for low confidence context"],
            "expected": "Citation requirements and fallback behavior are satisfied",
        },
    ]
    known_gaps = ["Live vector index latency and reranker quality checks are not auto-generated in v1.7."]
    assumptions = [f"Coverage focus: {', '.join(strategy.coverage_focus) or 'rag_app defaults'}"]
    return checklist, testcases, known_gaps, assumptions


def _workflow_assets(intake: NormalizedIntake, strategy: StrategyPlan) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    checklist = [
        {"id": "WF-CHK-001", "item": "Trigger payload contract is defined", "priority": "P0"},
        {"id": "WF-CHK-002", "item": "Step chain and transition definitions are present", "priority": "P0"},
        {"id": "WF-CHK-003", "item": "Error recovery policy is configured", "priority": "P1"},
        {"id": "WF-CHK-004", "item": "Idempotency baseline is declared", "priority": "P1"},
    ]
    testcases = [
        {
            "id": "WF-TC-001",
            "title": "Trigger and step-chain validation",
            "type": "workflow-chain",
            "steps": ["Apply trigger payload", "Validate ordered step chain", "Capture transition traces"],
            "expected": "Workflow chain initializes and transitions correctly",
        },
        {
            "id": "WF-TC-002",
            "title": "Recovery and idempotency smoke",
            "type": "workflow-recovery",
            "steps": ["Validate retry policy and error branch metadata", "Validate idempotency key handling"],
            "expected": "Workflow can recover and avoid duplicate side effects in smoke mode",
        },
    ]
    known_gaps = ["Distributed orchestration timing checks are not auto-generated in v1.7."]
    assumptions = [f"Strategy priorities: {', '.join(strategy.execution_priorities) or 'workflow defaults'}"]
    return checklist, testcases, known_gaps, assumptions


def _data_pipeline_assets(intake: NormalizedIntake, strategy: StrategyPlan) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    checklist = [
        {"id": "DP-CHK-001", "item": "Schema and batch artifacts are configured", "priority": "P0"},
        {"id": "DP-CHK-002", "item": "Expected column contract is defined", "priority": "P0"},
        {"id": "DP-CHK-003", "item": "Transformation list is declared", "priority": "P1"},
        {"id": "DP-CHK-004", "item": "Batch failure handling/logging expectations exist", "priority": "P1"},
    ]
    testcases = [
        {
            "id": "DP-TC-001",
            "title": "Schema consistency smoke",
            "type": "pipeline-schema",
            "steps": ["Load schema artifact", "Validate expected columns", "Capture schema validation traces"],
            "expected": "Schema contract remains consistent with expectations",
        },
        {
            "id": "DP-TC-002",
            "title": "Data integrity and transformation smoke",
            "type": "pipeline-integrity",
            "steps": ["Load sample batch", "Validate expected fields in records", "Validate transformation declarations"],
            "expected": "Data integrity baseline is met and transformation chain is declared",
        },
    ]
    known_gaps = ["Large-scale throughput and performance checks are not auto-generated in v1.7."]
    assumptions = [f"Coverage focus: {', '.join(strategy.coverage_focus) or 'data_pipeline defaults'}"]
    return checklist, testcases, known_gaps, assumptions


def _render_checklist_markdown(project_type: str, checklist: list[dict[str, Any]]) -> str:
    lines = [f"# {project_type.upper()} Checklist", "", "| ID | Item | Priority |", "|---|---|---|"]
    for item in checklist:
        lines.append(f"| {item['id']} | {item['item']} | {item['priority']} |")
    return "\n".join(lines) + "\n"


def _render_testcases_markdown(project_type: str, testcases: list[dict[str, Any]]) -> str:
    lines = [f"# {project_type.upper()} Test Cases", ""]
    for testcase in testcases:
        lines.append(f"## {testcase['id']} - {testcase['title']}")
        lines.append(f"- Type: {testcase['type']}")
        lines.append("- Steps:")
        for step in testcase["steps"]:
            lines.append(f"  - {step}")
        lines.append(f"- Expected: {testcase['expected']}")
        lines.append("")
    return "\n".join(lines)


def _bug_report_template(project_type: str, project_name: str) -> str:
    return f"""# Bug Report Template ({project_type.upper()})

## Metadata
- Project: {project_name}
- Product Type: {project_type}
- Environment:
- Build/Version:

## Summary
- Title:
- Severity: (blocker/critical/high/medium/low)
- Expected:
- Actual:

## Reproduction Steps
1.
2.
3.

## Evidence
- Logs:
- Screenshots:
- Traces:
- Artifacts:

## Impact
- Release Gate Impact:
- Workaround:
"""


def generate_assets(
    intake: NormalizedIntake,
    product_type: str,
    strategy: StrategyPlan,
    config: RuntimeConfig,
) -> GeneratedAssetBundle:
    if product_type == "api":
        checklist, testcases, known_gaps, assumptions = _api_assets(intake, strategy)
    elif product_type == "model":
        checklist, testcases, known_gaps, assumptions = _model_assets(intake, strategy)
    elif product_type == "mobile":
        checklist, testcases, known_gaps, assumptions = _mobile_assets(intake, strategy)
    elif product_type == "llm_app":
        checklist, testcases, known_gaps, assumptions = _llm_app_assets(intake, strategy)
    elif product_type == "rag_app":
        checklist, testcases, known_gaps, assumptions = _rag_app_assets(intake, strategy)
    elif product_type == "workflow":
        checklist, testcases, known_gaps, assumptions = _workflow_assets(intake, strategy)
    elif product_type == "data_pipeline":
        checklist, testcases, known_gaps, assumptions = _data_pipeline_assets(intake, strategy)
    else:
        checklist, testcases, known_gaps, assumptions = _web_assets(intake, strategy)

    checklist_payload = {
        "project_name": intake.name,
        "project_type": product_type,
        "manifest_path": intake.manifest_path,
        "items": checklist,
    }
    testcases_payload = {
        "project_name": intake.name,
        "project_type": product_type,
        "manifest_path": intake.manifest_path,
        "cases": testcases,
    }

    checklist_path = Path(config.paths.latest_checklist_file)
    checklist_md_path = Path(config.paths.latest_checklist_markdown_file)
    testcases_path = Path(config.paths.latest_testcases_file)
    testcases_md_path = Path(config.paths.latest_testcases_markdown_file)
    bug_template_path = Path(config.paths.latest_bug_report_template_file)
    index_path = Path(config.paths.latest_generated_assets_index_file)

    checklist_path.parent.mkdir(parents=True, exist_ok=True)
    checklist_md_path.parent.mkdir(parents=True, exist_ok=True)
    testcases_path.parent.mkdir(parents=True, exist_ok=True)
    testcases_md_path.parent.mkdir(parents=True, exist_ok=True)
    bug_template_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    checklist_path.write_text(json.dumps(checklist_payload, indent=2), encoding="utf-8")
    checklist_md_path.write_text(_render_checklist_markdown(product_type, checklist), encoding="utf-8")
    testcases_path.write_text(json.dumps(testcases_payload, indent=2), encoding="utf-8")
    testcases_md_path.write_text(_render_testcases_markdown(product_type, testcases), encoding="utf-8")
    bug_template_path.write_text(_bug_report_template(product_type, intake.name), encoding="utf-8")

    artifact_paths = [
        str(checklist_path),
        str(checklist_md_path),
        str(testcases_path),
        str(testcases_md_path),
        str(bug_template_path),
    ]

    index_payload = {
        "project_name": intake.name,
        "project_type": product_type,
        "manifest_path": intake.manifest_path,
        "artifact_paths": artifact_paths,
        "known_gaps": known_gaps,
        "assumptions": assumptions,
    }
    index_path.write_text(json.dumps(index_payload, indent=2), encoding="utf-8")
    artifact_paths.append(str(index_path))

    return GeneratedAssetBundle(
        project_type=product_type,
        checklist=checklist,
        testcases=testcases,
        known_gaps=known_gaps,
        assumptions=assumptions,
        artifact_paths=artifact_paths,
    )
