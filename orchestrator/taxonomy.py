from __future__ import annotations

from pydantic import BaseModel, Field

from orchestrator.capabilities import CORE_CAPABILITIES, Capability, capability_names


class TaxonomyProfile(BaseModel):
    product_type: str
    default_dimensions: list[str] = Field(default_factory=list)
    default_risks: list[str] = Field(default_factory=list)
    planning_priorities: list[str] = Field(default_factory=list)
    coverage_focus: list[str] = Field(default_factory=list)
    capability_expectations: list[str] = Field(default_factory=list)


def _default_capability_expectations() -> list[str]:
    return capability_names(CORE_CAPABILITIES)


def _profile(
    product_type: str,
    dimensions: list[str],
    risks: list[str],
    priorities: list[str],
    coverage_focus: list[str],
    capabilities: list[Capability] | None = None,
) -> TaxonomyProfile:
    capability_values = _default_capability_expectations() if capabilities is None else capability_names(capabilities)
    return TaxonomyProfile(
        product_type=product_type,
        default_dimensions=dimensions,
        default_risks=risks,
        planning_priorities=priorities,
        coverage_focus=coverage_focus,
        capability_expectations=capability_values,
    )


TAXONOMY_BY_PRODUCT: dict[str, TaxonomyProfile] = {
    "web": _profile(
        "web",
        dimensions=["navigation", "auth", "workflow", "basic usability"],
        risks=["unreachable routes", "auth breakage", "critical workflow regressions"],
        priorities=["P0: reachability", "P1: auth path", "P2: feature workflow smoke"],
        coverage_focus=["journey coverage", "auth gate", "core feature smoke"],
    ),
    "api": _profile(
        "api",
        dimensions=["availability", "contract", "auth", "negative behavior"],
        risks=["5xx regressions", "payload contract drift", "auth failures"],
        priorities=["P0: endpoint availability", "P1: status/code consistency", "P2: payload validation"],
        coverage_focus=["endpoint matrix", "contract smoke", "negative status handling"],
    ),
    "model": _profile(
        "model",
        dimensions=["quality", "consistency", "safety", "threshold conformance"],
        risks=["quality threshold misses", "dataset skew", "endpoint instability"],
        priorities=["P0: dataset and labels readiness", "P1: metric computation", "P2: live inference smoke"],
        coverage_focus=["evaluation dimensions", "metrics + thresholds", "metadata sanity"],
    ),
    "mobile": _profile(
        "mobile",
        dimensions=["install/open", "navigation", "permissions", "auth", "stability"],
        risks=["app launch failure", "permission denial regressions", "navigation dead-ends", "crash-prone flows"],
        priorities=["P0: install/open path", "P1: navigation smoke", "P1: permission handling", "P2: auth/usability"],
        coverage_focus=["launch readiness", "permission gates", "critical journey smoke"],
    ),
    "llm_app": _profile(
        "llm_app",
        dimensions=["response quality", "consistency", "safety", "tool-use readiness", "fallback handling"],
        risks=["unsafe output", "inconsistent responses", "tool call failures", "fallback misbehavior"],
        priorities=["P0: safety + fallback checks", "P1: consistency checks", "P2: tool-use readiness smoke"],
        coverage_focus=["prompt-response quality", "safety policy checks", "tool/fallback behavior"],
    ),
    "rag_app": _profile(
        "rag_app",
        dimensions=["prompt-response quality", "retrieval grounding", "citation quality", "context readiness", "safety"],
        risks=["hallucination", "missing citations", "weak grounding", "context retrieval misses"],
        priorities=["P0: retrieval grounding", "P0: citation checks", "P1: quality checks", "P2: tool/context readiness"],
        coverage_focus=["grounded answer quality", "citation expectations", "retrieval context coverage"],
    ),
    "workflow": _profile(
        "workflow",
        dimensions=["trigger validation", "step chaining", "state transition correctness", "error recovery", "idempotency"],
        risks=["broken step orchestration", "invalid transitions", "duplicate execution side effects", "recovery gaps"],
        priorities=["P0: trigger + step chain", "P1: transition correctness", "P1: recovery/idempotency checks"],
        coverage_focus=["trigger inputs", "state transitions", "recovery and idempotency baselines"],
    ),
    "data_pipeline": _profile(
        "data_pipeline",
        dimensions=["schema consistency", "transformation correctness", "data integrity", "batch handling", "observability"],
        risks=["schema drift", "transformation regressions", "data loss", "batch failure handling gaps"],
        priorities=["P0: schema and integrity", "P1: transformation checks", "P1: batch success/failure handling"],
        coverage_focus=["schema contract", "integrity checks", "batch and logging smoke"],
    ),
}


def get_taxonomy_profile(product_type: str) -> TaxonomyProfile:
    normalized = (product_type or "").lower().strip()
    if normalized in TAXONOMY_BY_PRODUCT:
        return TAXONOMY_BY_PRODUCT[normalized]
    return TAXONOMY_BY_PRODUCT["web"]


def supported_taxonomy_product_types() -> list[str]:
    return sorted(TAXONOMY_BY_PRODUCT.keys())
