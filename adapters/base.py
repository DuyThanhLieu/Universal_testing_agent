from __future__ import annotations

from abc import ABC, abstractmethod

from orchestrator.config import RuntimeConfig
from orchestrator.models import (
    AdapterPlan,
    DiscoveryResult,
    EvidenceBundle,
    ExecutionResult,
    GeneratedAssets,
    NormalizedIntake,
    StrategyPlan,
)


class BaseAdapter(ABC):
    name: str = "base"

    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config

    @abstractmethod
    def discover(self, intake: NormalizedIntake) -> DiscoveryResult:
        raise NotImplementedError

    @abstractmethod
    def plan(self, intake: NormalizedIntake, strategy: StrategyPlan) -> AdapterPlan:
        raise NotImplementedError

    @abstractmethod
    def generate_assets(self, intake: NormalizedIntake, adapter_plan: AdapterPlan) -> GeneratedAssets:
        raise NotImplementedError

    @abstractmethod
    def execute(self, intake: NormalizedIntake, generated_assets: GeneratedAssets) -> ExecutionResult:
        raise NotImplementedError

    @abstractmethod
    def collect_evidence(self, intake: NormalizedIntake, execution_result: ExecutionResult) -> EvidenceBundle:
        raise NotImplementedError
