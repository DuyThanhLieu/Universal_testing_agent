from orchestrator.models import CoverageStats, DefectSummary, SummaryStats
from orchestrator.policy import evaluate_release_policy


def test_policy_passes_when_rules_satisfied() -> None:
    policy = evaluate_release_policy(
        acceptance={
            "blockers_allowed": 0,
            "critical_allowed": 0,
            "minimum_coverage": 0.5,
            "max_failed": 1,
        },
        summary=SummaryStats(total_checks=5, passed=4, failed=1, blocked=0, skipped=0),
        coverage=CoverageStats(planned_cases=5, executed_cases=5, execution_rate=1.0, requirement_coverage=0.8),
        defects=DefectSummary(blocker=0, critical=0, high=0, medium=1, low=0),
    )
    assert policy.release_ready is True
    assert policy.verdict == "pass"
    assert policy.reasons == []


def test_policy_fails_when_rules_violated() -> None:
    policy = evaluate_release_policy(
        acceptance={
            "blockers_allowed": 0,
            "critical_allowed": 0,
            "minimum_coverage": 0.9,
            "max_failed": 0,
        },
        summary=SummaryStats(total_checks=5, passed=2, failed=3, blocked=0, skipped=0),
        coverage=CoverageStats(planned_cases=5, executed_cases=5, execution_rate=1.0, requirement_coverage=0.4),
        defects=DefectSummary(blocker=1, critical=1, high=0, medium=0, low=0),
    )
    assert policy.release_ready is False
    assert policy.verdict == "fail"
    assert len(policy.reasons) >= 3
