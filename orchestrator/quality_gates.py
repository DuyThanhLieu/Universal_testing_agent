from __future__ import annotations

from typing import Any

from orchestrator.models import ContractValidationResult, CoverageStats, DefectSummary, QualityGateResult, SummaryStats


def _rule_value(acceptance: dict[str, Any], key: str, default: Any) -> Any:
    if key in acceptance:
        return acceptance[key]
    gates = acceptance.get("quality_gates")
    if isinstance(gates, dict) and key in gates:
        return gates[key]
    policy = acceptance.get("policy")
    if isinstance(policy, dict) and key in policy:
        return policy[key]
    return default


def evaluate_quality_gates(
    *,
    acceptance: dict[str, Any],
    summary: SummaryStats,
    coverage: CoverageStats,
    defects: DefectSummary,
    contract_validation: ContractValidationResult | None = None,
    fallback_mode: str = "native",
) -> QualityGateResult:
    max_critical_defects = int(_rule_value(acceptance, "max_critical_defects", _rule_value(acceptance, "critical_allowed", 0)))
    max_failed_tests = int(_rule_value(acceptance, "max_failed_tests", _rule_value(acceptance, "max_failed", 0)))
    minimum_coverage = float(_rule_value(acceptance, "minimum_coverage", _rule_value(acceptance, "coverage_threshold", 0.7)))
    contract_validation_required = bool(_rule_value(acceptance, "contract_validation_required", False))
    fallback_not_allowed = bool(_rule_value(acceptance, "fallback_not_allowed", False))

    gate_reasons: list[str] = []
    blocking_issues: list[str] = []
    warning_issues: list[str] = []

    if defects.critical > max_critical_defects:
        issue = f"Critical defects {defects.critical} exceed allowed {max_critical_defects}."
        gate_reasons.append(issue)
        blocking_issues.append(issue)

    if summary.failed > max_failed_tests:
        issue = f"Failed checks {summary.failed} exceed allowed {max_failed_tests}."
        gate_reasons.append(issue)
        blocking_issues.append(issue)

    if coverage.requirement_coverage < minimum_coverage:
        issue = (
            f"Requirement coverage {coverage.requirement_coverage} is below minimum {minimum_coverage}."
        )
        gate_reasons.append(issue)
        blocking_issues.append(issue)

    if contract_validation_required:
        if contract_validation is None:
            issue = "Contract validation is required but no contract validation result is available."
            gate_reasons.append(issue)
            blocking_issues.append(issue)
        elif not contract_validation.release_ready:
            issue = "Contract validation did not pass while contract validation is required."
            gate_reasons.append(issue)
            blocking_issues.append(issue)

    if fallback_not_allowed and fallback_mode != "native":
        issue = f"Fallback mode '{fallback_mode}' is not allowed by quality gate policy."
        gate_reasons.append(issue)
        blocking_issues.append(issue)

    if summary.blocked > 0:
        warning_issues.append(f"{summary.blocked} checks are blocked.")

    gate_status = "pass"
    if blocking_issues:
        gate_status = "fail"
    elif warning_issues:
        gate_status = "warning"
        gate_reasons.extend(warning_issues)

    recommendation = "Ready for release gate promotion."
    if gate_status == "warning":
        recommendation = "Proceed with caution; warnings should be addressed."
    elif gate_status == "fail":
        recommendation = "Do not release until blocking quality gate issues are fixed."

    evaluated_rules = {
        "max_critical_defects": max_critical_defects,
        "max_failed_tests": max_failed_tests,
        "minimum_coverage": minimum_coverage,
        "contract_validation_required": contract_validation_required,
        "fallback_not_allowed": fallback_not_allowed,
        "observed": {
            "critical_defects": defects.critical,
            "failed_checks": summary.failed,
            "blocked_checks": summary.blocked,
            "requirement_coverage": coverage.requirement_coverage,
            "fallback_mode": fallback_mode,
            "contract_release_ready": contract_validation.release_ready if contract_validation else None,
        },
    }

    return QualityGateResult(
        gate_status=gate_status,
        gate_reasons=gate_reasons,
        blocking_issues=blocking_issues,
        recommendation=recommendation,
        evaluated_rules=evaluated_rules,
    )
