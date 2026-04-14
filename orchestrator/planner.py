from __future__ import annotations

from typing import Any

from orchestrator.models import NormalizedIntake, StrategyPlan
from orchestrator.taxonomy import TaxonomyProfile, get_taxonomy_profile


def _as_constraints(value: list[str] | dict[str, object]) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, dict):
        return [f"{key}: {value[key]}" for key in value]
    return []


def _base_plan(intake: NormalizedIntake, taxonomy: TaxonomyProfile) -> dict[str, Any]:
    return {
        "scope": [
            f"Project scope: {intake.name}",
            f"Primary target: {intake.target or intake.url or 'offline-skeleton'}",
        ],
        "risks": list(taxonomy.default_risks),
        "coverage": {
            "focus": taxonomy.coverage_focus,
            "dimensions": taxonomy.default_dimensions,
        },
        "coverage_focus": list(taxonomy.coverage_focus),
        "execution_priorities": list(taxonomy.planning_priorities),
        "capability_expectations": list(taxonomy.capability_expectations),
        "taxonomy_dimensions": list(taxonomy.default_dimensions),
        "constraints": _as_constraints(intake.constraints),
    }


def _build_web_plan(intake: NormalizedIntake, taxonomy: TaxonomyProfile) -> StrategyPlan:
    plan = _base_plan(intake, taxonomy)
    plan["scope"].extend(
        [
            "Web landing and critical routes",
            f"Feature focus: {intake.feature or intake.request.get('feature') or 'primary workflow'}",
        ]
    )
    plan["coverage"].update({"functional": "smoke", "auth": "basic", "negative": "basic"})
    if not plan["constraints"]:
        plan["constraints"] = ["Use non-destructive smoke workflow checks only."]
    return StrategyPlan(**plan)


def _build_api_plan(intake: NormalizedIntake, taxonomy: TaxonomyProfile) -> StrategyPlan:
    plan = _base_plan(intake, taxonomy)
    endpoints = intake.request.get("endpoints", ["/"])
    endpoint_matrix_summary = [
        {"endpoint": str(endpoint), "method": "GET", "checks": ["status", "payload_basic_shape"]}
        for endpoint in endpoints
    ]
    plan["scope"].extend(
        [
            "API endpoint smoke and contract checks",
            f"Base URL: {intake.api.get('base_url') or intake.target or 'simulation'}",
        ]
    )
    plan["risks"].extend(["status code regressions", "payload contract drift"])
    plan["coverage"].update(
        {
            "endpoint_matrix": len(endpoint_matrix_summary),
            "auth_coverage": "basic",
            "contract_coverage": "smoke",
            "negative_coverage": "basic",
        }
    )
    plan["endpoint_matrix_summary"] = endpoint_matrix_summary
    return StrategyPlan(**plan)


def _build_model_plan(intake: NormalizedIntake, taxonomy: TaxonomyProfile) -> StrategyPlan:
    plan = _base_plan(intake, taxonomy)
    threshold = float(intake.acceptance.get("quality_threshold", 0.7))
    metrics = ["label_coverage", "sample_count", "quality_score_proxy"]
    plan["scope"].extend(["Model metadata and dataset readiness", "Evaluation case processing"])
    plan["evaluation_dimensions"] = [
        "label alignment",
        "response format consistency",
        "threshold conformance",
    ]
    plan["metrics_to_compute"] = metrics
    plan["coverage"].update({"metrics": metrics, "threshold": threshold})
    plan["threshold_risk_notes"] = [
        f"Quality threshold target: {threshold}",
        "Endpoint unavailability will use deterministic local fallback.",
    ]
    return StrategyPlan(**plan)


def _build_mobile_plan(intake: NormalizedIntake, taxonomy: TaxonomyProfile) -> StrategyPlan:
    plan = _base_plan(intake, taxonomy)
    permissions = intake.request.get("permissions") or intake.environment.get("permissions") or []
    plan["scope"].extend(
        [
            "Install/open path validation",
            "Navigation and basic usability smoke",
            "Permission and auth gate checks",
        ]
    )
    plan["coverage"].update(
        {
            "navigation": "smoke",
            "permissions": [str(item) for item in permissions] if isinstance(permissions, list) else [],
            "auth": "config-smoke",
            "stability": "basic crash indicators",
        }
    )
    plan["risks"].extend(["permission flow regressions", "launch instability"])
    return StrategyPlan(**plan)


def _build_llm_app_plan(intake: NormalizedIntake, taxonomy: TaxonomyProfile) -> StrategyPlan:
    plan = _base_plan(intake, taxonomy)
    eval_cases = intake.request.get("eval_cases") or []
    tools = intake.request.get("tools") or []
    plan["scope"].extend(
        [
            "Prompt-response quality and consistency smoke checks",
            "Safety and fallback behavior validation",
            "Tool-use readiness checks",
        ]
    )
    plan["coverage"].update(
        {
            "eval_case_count": len(eval_cases),
            "tool_count": len(tools),
            "safety": "policy/signal smoke",
            "fallback": intake.request.get("fallback_strategy", "not_declared"),
        }
    )
    plan["evaluation_dimensions"] = [
        "prompt quality",
        "response consistency",
        "safety behavior",
        "tool-use readiness",
        "fallback handling",
    ]
    plan["metrics_to_compute"] = ["consistency_proxy", "safety_signal_ratio", "tool_readiness_ratio"]
    plan["threshold_risk_notes"] = [
        "Safety drift should block release for llm_app flows.",
        "Missing fallback strategy increases runtime incident risk.",
    ]
    return StrategyPlan(**plan)


def _build_rag_app_plan(intake: NormalizedIntake, taxonomy: TaxonomyProfile) -> StrategyPlan:
    plan = _base_plan(intake, taxonomy)
    eval_cases = intake.request.get("eval_cases") or []
    tools = intake.request.get("tools") or []
    plan["scope"].extend(
        [
            "Retrieval-grounded prompt/response quality checks",
            "Citation and hallucination-risk smoke checks",
            "Context/tool readiness and fallback handling checks",
        ]
    )
    plan["coverage"].update(
        {
            "eval_case_count": len(eval_cases),
            "tool_count": len(tools),
            "retrieval_grounding": "smoke",
            "citation_expectations": bool(intake.request.get("require_citations", False)),
            "fallback": intake.request.get("fallback_strategy", "not_declared"),
        }
    )
    plan["evaluation_dimensions"] = [
        "prompt-response quality",
        "retrieval grounding",
        "hallucination risk",
        "citation expectations",
        "context/tool readiness",
    ]
    plan["metrics_to_compute"] = ["grounding_proxy", "citation_hit_ratio", "hallucination_risk_proxy"]
    plan["threshold_risk_notes"] = [
        "Ungrounded responses should fail rag_app release gate.",
        "Missing citations on citation-required flows should fail smoke quality checks.",
    ]
    return StrategyPlan(**plan)


def _build_workflow_plan(intake: NormalizedIntake, taxonomy: TaxonomyProfile) -> StrategyPlan:
    plan = _base_plan(intake, taxonomy)
    steps = intake.request.get("steps") or []
    transitions = intake.request.get("transitions") or []
    plan["scope"].extend(
        [
            "Trigger/input validation",
            "Step chaining and state transition correctness",
            "Error recovery and idempotency baseline checks",
        ]
    )
    plan["coverage"].update(
        {
            "step_count": len(steps),
            "transition_count": len(transitions),
            "trigger_validation": "smoke",
            "recovery_validation": "config-smoke",
            "idempotency": "basic",
        }
    )
    return StrategyPlan(**plan)


def _build_data_pipeline_plan(intake: NormalizedIntake, taxonomy: TaxonomyProfile) -> StrategyPlan:
    plan = _base_plan(intake, taxonomy)
    expected_columns = intake.request.get("expected_columns") or []
    transformations = intake.request.get("transformations") or []
    plan["scope"].extend(
        [
            "Schema consistency and contract checks",
            "Transformation correctness and data integrity checks",
            "Batch success/failure handling and observability smoke checks",
        ]
    )
    plan["coverage"].update(
        {
            "expected_columns": [str(item) for item in expected_columns] if isinstance(expected_columns, list) else [],
            "transformations": [str(item) for item in transformations] if isinstance(transformations, list) else [],
            "batch_handling": "smoke",
            "observability": "log trace verification",
        }
    )
    return StrategyPlan(**plan)


def generate_test_strategy(intake: NormalizedIntake, product_type: str) -> StrategyPlan:
    normalized = (product_type or "").lower().strip()
    taxonomy = get_taxonomy_profile(normalized)
    if normalized == "api":
        return _build_api_plan(intake, taxonomy)
    if normalized == "model":
        return _build_model_plan(intake, taxonomy)
    if normalized == "mobile":
        return _build_mobile_plan(intake, taxonomy)
    if normalized == "llm_app":
        return _build_llm_app_plan(intake, taxonomy)
    if normalized == "rag_app":
        return _build_rag_app_plan(intake, taxonomy)
    if normalized == "workflow":
        return _build_workflow_plan(intake, taxonomy)
    if normalized == "data_pipeline":
        return _build_data_pipeline_plan(intake, taxonomy)
    return _build_web_plan(intake, taxonomy)
