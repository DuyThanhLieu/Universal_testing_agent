from __future__ import annotations

from typing import Any

from orchestrator.models import CoverageStats, DefectSummary, PolicyEvaluation, SummaryStats


def _rule_value(acceptance: dict[str, Any], key: str, default: Any) -> Any:
    if key in acceptance:
        return acceptance[key]
    policy = acceptance.get("policy", {})
    if isinstance(policy, dict) and key in policy:
        return policy[key]
    return default


def evaluate_release_policy(
    acceptance: dict[str, Any],
    summary: SummaryStats,
    coverage: CoverageStats,
    defects: DefectSummary,
) -> PolicyEvaluation:
    blockers_allowed = int(_rule_value(acceptance, "blockers_allowed", 0))
    critical_allowed = int(_rule_value(acceptance, "critical_allowed", 0))
    minimum_coverage = float(_rule_value(acceptance, "minimum_coverage", _rule_value(acceptance, "coverage_threshold", 0.7)))
    max_failed = int(_rule_value(acceptance, "max_failed", 0))

    reasons: list[str] = []
    if defects.blocker > blockers_allowed:
        reasons.append(f"Blocker defects {defects.blocker} exceed allowed {blockers_allowed}.")
    if defects.critical > critical_allowed:
        reasons.append(f"Critical defects {defects.critical} exceed allowed {critical_allowed}.")
    if coverage.requirement_coverage < minimum_coverage:
        reasons.append(
            f"Requirement coverage {coverage.requirement_coverage} is below minimum {minimum_coverage}."
        )
    if summary.failed > max_failed:
        reasons.append(f"Failed checks {summary.failed} exceed allowed {max_failed}.")

    evaluated_rules = {
        "blockers_allowed": blockers_allowed,
        "critical_allowed": critical_allowed,
        "minimum_coverage": minimum_coverage,
        "max_failed": max_failed,
        "observed": {
            "failed": summary.failed,
            "blocker": defects.blocker,
            "critical": defects.critical,
            "requirement_coverage": coverage.requirement_coverage,
        },
    }
    release_ready = len(reasons) == 0
    verdict = "pass" if release_ready else "fail"
    return PolicyEvaluation(
        release_ready=release_ready,
        verdict=verdict,
        reasons=reasons,
        evaluated_rules=evaluated_rules,
    )
