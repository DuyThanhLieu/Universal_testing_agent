from __future__ import annotations

from enum import Enum


class Capability(str, Enum):
    DISCOVERY = "discovery"
    CLASSIFICATION = "classification"
    PLANNING = "planning"
    ASSET_GENERATION = "asset_generation"
    CONTRACT_VALIDATION = "contract_validation"
    EXECUTION_SMOKE = "execution_smoke"
    POLICY_EVALUATION = "policy_evaluation"
    HISTORY_TRACKING = "history_tracking"
    TREND_ANALYSIS = "trend_analysis"
    COMPARISON = "comparison"
    REPORTING = "reporting"


CORE_CAPABILITIES: tuple[Capability, ...] = (
    Capability.DISCOVERY,
    Capability.CLASSIFICATION,
    Capability.PLANNING,
    Capability.ASSET_GENERATION,
    Capability.CONTRACT_VALIDATION,
    Capability.EXECUTION_SMOKE,
    Capability.POLICY_EVALUATION,
    Capability.HISTORY_TRACKING,
    Capability.TREND_ANALYSIS,
    Capability.COMPARISON,
    Capability.REPORTING,
)


def capability_names(capabilities: list[Capability] | tuple[Capability, ...]) -> list[str]:
    return [capability.value for capability in capabilities]
