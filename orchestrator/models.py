from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class UtaModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class Artifact(UtaModel):
    name: str = "artifact"
    type: str = "generic"
    path: str | None = None
    url: str | None = None
    labels: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntakeManifest(UtaModel):
    name: str = "unnamed-project"
    project_type: str = "auto"
    project_subtype: str | None = None
    url: str | None = None
    labels: list[str] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    interfaces: list[dict[str, Any]] = Field(default_factory=list)
    entry_points: list[dict[str, Any]] = Field(default_factory=list)
    environment: dict[str, Any] = Field(default_factory=dict)
    request: dict[str, Any] = Field(default_factory=dict)
    acceptance: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    oracle: dict[str, Any] = Field(default_factory=dict)
    baseline: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] | dict[str, Any] = Field(default_factory=list)
    dimensions: list[str] | dict[str, Any] = Field(default_factory=list)
    auth: dict[str, Any] = Field(default_factory=dict)
    feature: str | None = None
    constraints: list[str] | dict[str, Any] = Field(default_factory=list)
    api: dict[str, Any] = Field(default_factory=dict)
    model: dict[str, Any] = Field(default_factory=dict)


class NormalizedIntake(UtaModel):
    manifest_path: str
    name: str
    project_type: str
    project_subtype: str | None = None
    url: str | None = None
    target: str | None = None
    feature: str | None = None
    labels: list[str] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    interfaces: list[dict[str, Any]] = Field(default_factory=list)
    entry_points: list[dict[str, Any]] = Field(default_factory=list)
    environment: dict[str, Any] = Field(default_factory=dict)
    request: dict[str, Any] = Field(default_factory=dict)
    acceptance: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    oracle: dict[str, Any] = Field(default_factory=dict)
    baseline: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] | dict[str, Any] = Field(default_factory=list)
    dimensions: list[str] | dict[str, Any] = Field(default_factory=list)
    auth: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] | dict[str, Any] = Field(default_factory=list)
    api: dict[str, Any] = Field(default_factory=dict)
    model: dict[str, Any] = Field(default_factory=dict)


class StrategyPlan(UtaModel):
    scope: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    coverage: dict[str, Any] = Field(default_factory=dict)
    coverage_focus: list[str] = Field(default_factory=list)
    execution_priorities: list[str] = Field(default_factory=list)
    capability_expectations: list[str] = Field(default_factory=list)
    taxonomy_dimensions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    endpoint_matrix_summary: list[dict[str, Any]] = Field(default_factory=list)
    evaluation_dimensions: list[str] = Field(default_factory=list)
    metrics_to_compute: list[str] = Field(default_factory=list)
    threshold_risk_notes: list[str] = Field(default_factory=list)


class DiscoveryResult(UtaModel):
    items: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AdapterPlan(UtaModel):
    steps: list[str] = Field(default_factory=list)
    coverage: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GeneratedAssets(UtaModel):
    artifacts: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SummaryStats(UtaModel):
    total_checks: int = 0
    passed: int = 0
    failed: int = 0
    blocked: int = 0
    skipped: int = 0


class CoverageStats(UtaModel):
    planned_cases: int = 0
    executed_cases: int = 0
    execution_rate: float = 0.0
    requirement_coverage: float = 0.0


class DefectDetail(UtaModel):
    id: str
    severity: Literal["blocker", "critical", "high", "medium", "low"] = "medium"
    category: Literal["functional", "contract", "performance", "data", "model"] = "functional"
    reproducibility: Literal["deterministic", "flaky", "unknown"] = "deterministic"
    confidence_score: float = 1.0
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class DefectSummary(UtaModel):
    blocker: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class EvidenceBundle(UtaModel):
    logs: list[str] = Field(default_factory=list)
    screenshots: list[str] = Field(default_factory=list)
    traces: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)


class Recommendation(UtaModel):
    release_ready: bool = False
    notes: list[str] = Field(default_factory=list)


class PolicyEvaluation(UtaModel):
    release_ready: bool = False
    verdict: str = "fail"
    reasons: list[str] = Field(default_factory=list)
    evaluated_rules: dict[str, Any] = Field(default_factory=dict)


class QualityGateResult(UtaModel):
    gate_status: Literal["pass", "fail", "warning"] = "warning"
    gate_reasons: list[str] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    recommendation: str = "Review quality gate findings."
    evaluated_rules: dict[str, Any] = Field(default_factory=dict)


class RunMetadata(UtaModel):
    run_id: str
    command: str
    project_name: str
    project_type: str
    manifest_path: str
    started_at: str
    finished_at: str
    duration_seconds: float
    status: str
    artifact_dir: str


class PluginValidationSummary(UtaModel):
    plugin_name: str | None = None
    valid: bool = False
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    adapter_method_coverage: list[str] = Field(default_factory=list)
    capability_completeness: float = 0.0
    missing_recommended_capabilities: list[str] = Field(default_factory=list)
    support_level: str = "partial"
    fallback_support_note: str | None = None


class PluginReportContext(UtaModel):
    plugin_name: str
    plugin_version: str
    author: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    compatibility: dict[str, Any] = Field(default_factory=dict)
    supported_product_types: list[str] = Field(default_factory=list)
    supported_capabilities: list[str] = Field(default_factory=list)
    fallback_mode: str = "native"
    adapter_target: str
    health_metadata: dict[str, Any] = Field(default_factory=dict)
    discovered_from: str = "builtin"


class PluginOnboardingResult(UtaModel):
    plugin_name: str
    onboarding_status: str = "partial"
    completeness_score: float = 0.0
    missing_items: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CoverageCatalogEntry(UtaModel):
    plugin_name: str
    plugin_version: str
    author: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    compatibility: dict[str, Any] = Field(default_factory=dict)
    product_types: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    support_level: str = "partial"
    fallback_mode: str = "native"
    fallback_note: str | None = None
    missing_recommended_capabilities: list[str] = Field(default_factory=list)
    onboarding_status: str = "partial"


class CoverageCatalogSummary(UtaModel):
    generated_at: str
    entries: list[CoverageCatalogEntry] = Field(default_factory=list)


class HistoryRecord(UtaModel):
    run_id: str
    timestamp: str
    project_name: str
    project_type: str
    adapter: str
    status: str
    summary: SummaryStats
    coverage: CoverageStats
    defects: DefectSummary
    release_ready: bool


class TrendAnalysis(UtaModel):
    runs_analyzed: int = 0
    overall_direction: Literal["improving", "stable", "degrading"] = "stable"
    pass_rate_trend: Literal["improving", "stable", "degrading"] = "stable"
    coverage_trend: Literal["improving", "stable", "degrading"] = "stable"
    defect_trend: Literal["improving", "stable", "degrading"] = "stable"
    release_readiness_trend: Literal["improving", "stable", "degrading"] = "stable"


class ContractValidationResult(UtaModel):
    release_ready: bool = False
    verdict: str = "fail"
    checks: dict[str, Any] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)


class ComparisonResult(UtaModel):
    current_result_path: str
    baseline_result_path: str
    changed: bool
    passed_delta: int
    failed_delta: int
    coverage_delta: float
    defect_delta: int
    release_ready_changed: bool
    regression_signals: list[str] = Field(default_factory=list)


class ExecutionResult(UtaModel):
    status: Literal["passed", "failed", "blocked", "error"] = "blocked"
    summary: SummaryStats = Field(default_factory=SummaryStats)
    coverage: CoverageStats = Field(default_factory=CoverageStats)
    defect_details: list[DefectDetail] = Field(default_factory=list)
    evidence: EvidenceBundle = Field(default_factory=EvidenceBundle)
    recommendation_notes: list[str] = Field(default_factory=list)
    raw_output: dict[str, Any] = Field(default_factory=dict)


class ExecutionEnvelope(UtaModel):
    run_id: str
    project_name: str
    project_type: str
    adapter: str
    status: Literal["passed", "failed", "blocked", "error"]
    started_at: str
    finished_at: str
    duration_seconds: float
    summary: SummaryStats
    coverage: CoverageStats
    defects: DefectSummary
    defect_details: list[DefectDetail] = Field(default_factory=list)
    evidence: EvidenceBundle
    recommendation: Recommendation
    plugin: PluginReportContext | None = None
    plugin_validation: PluginValidationSummary | None = None
    plugin_onboarding: PluginOnboardingResult | None = None
    support_level: str | None = None
    capability_path_used: list[str] = Field(default_factory=list)
    policy: PolicyEvaluation | None = None
    quality_gates: QualityGateResult | None = None
    run_metadata: RunMetadata | None = None
    generated_artifacts: list[str] = Field(default_factory=list)
    known_gaps: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_output: dict[str, Any] = Field(default_factory=dict)


class StandardReport(UtaModel):
    run_id: str
    project_name: str
    project_type: str
    adapter: str
    status: Literal["passed", "failed", "blocked", "error"]
    started_at: str
    finished_at: str
    duration_seconds: float
    summary: SummaryStats
    coverage: CoverageStats
    defects: DefectSummary
    defect_details: list[DefectDetail] = Field(default_factory=list)
    evidence: EvidenceBundle
    recommendation: Recommendation
    plugin: PluginReportContext | None = None
    plugin_validation: PluginValidationSummary | None = None
    plugin_onboarding: PluginOnboardingResult | None = None
    support_level: str | None = None
    coverage_catalog_reference: str | None = None
    capability_path_used: list[str] = Field(default_factory=list)
    policy: PolicyEvaluation
    quality_gates: QualityGateResult | None = None
    release_gate_summary: str
    known_gaps: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    artifact_references: list[str] = Field(default_factory=list)
    run_metadata: RunMetadata | None = None
    capabilities_used: list[str] = Field(default_factory=list)
    capability_coverage_summary: dict[str, Any] = Field(default_factory=dict)
    taxonomy_coverage_focus: list[str] = Field(default_factory=list)
    fallback_execution_note: str | None = None
    trend_summary: TrendAnalysis | None = None
    contract_validation_summary: ContractValidationResult | None = None
    comparison_summary: ComparisonResult | None = None
    regression_signals: list[str] = Field(default_factory=list)
    flaky_suspicion_note: str | None = None
    generated_at: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def defect_summary_from_details(defects: list[DefectDetail]) -> DefectSummary:
    counters = DefectSummary()
    for defect in defects:
        counters_value = getattr(counters, defect.severity)
        setattr(counters, defect.severity, counters_value + 1)
    return counters


def status_from_summary(summary: SummaryStats) -> Literal["passed", "failed", "blocked", "error"]:
    if summary.failed > 0:
        return "failed"
    if summary.blocked > 0:
        return "blocked"
    return "passed"
