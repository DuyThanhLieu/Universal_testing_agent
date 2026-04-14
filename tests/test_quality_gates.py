from orchestrator.models import ContractValidationResult, CoverageStats, DefectSummary, SummaryStats
from orchestrator.quality_gates import evaluate_quality_gates


def test_quality_gates_pass_with_strict_rules() -> None:
    gates = evaluate_quality_gates(
        acceptance={
            "max_critical_defects": 0,
            "max_failed_tests": 0,
            "minimum_coverage": 0.7,
            "contract_validation_required": True,
            "fallback_not_allowed": False,
        },
        summary=SummaryStats(total_checks=6, passed=6, failed=0, blocked=0, skipped=0),
        coverage=CoverageStats(planned_cases=6, executed_cases=6, execution_rate=1.0, requirement_coverage=0.8),
        defects=DefectSummary(blocker=0, critical=0, high=0, medium=0, low=0),
        contract_validation=ContractValidationResult(release_ready=True, verdict="pass", checks={}, reasons=[]),
        fallback_mode="native",
    )
    assert gates.gate_status == "pass"
    assert gates.blocking_issues == []


def test_quality_gates_fail_when_thresholds_violated() -> None:
    gates = evaluate_quality_gates(
        acceptance={
            "max_critical_defects": 0,
            "max_failed_tests": 0,
            "minimum_coverage": 0.9,
            "contract_validation_required": True,
            "fallback_not_allowed": True,
        },
        summary=SummaryStats(total_checks=6, passed=2, failed=3, blocked=1, skipped=0),
        coverage=CoverageStats(planned_cases=6, executed_cases=6, execution_rate=1.0, requirement_coverage=0.5),
        defects=DefectSummary(blocker=0, critical=1, high=1, medium=0, low=0),
        contract_validation=ContractValidationResult(release_ready=False, verdict="fail", checks={}, reasons=["x"]),
        fallback_mode="skeleton_smoke",
    )
    assert gates.gate_status == "fail"
    assert len(gates.blocking_issues) >= 3


def test_quality_gates_warning_on_blocked_checks() -> None:
    gates = evaluate_quality_gates(
        acceptance={},
        summary=SummaryStats(total_checks=1, passed=0, failed=0, blocked=1, skipped=0),
        coverage=CoverageStats(planned_cases=1, executed_cases=1, execution_rate=1.0, requirement_coverage=1.0),
        defects=DefectSummary(),
        contract_validation=None,
        fallback_mode="native",
    )
    assert gates.gate_status == "warning"
