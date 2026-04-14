from __future__ import annotations

from orchestrator.models import NormalizedIntake


def classify_product(intake: NormalizedIntake) -> str:
    explicit_type = (intake.project_type or "").lower()
    if explicit_type in {"web", "api", "model", "mobile", "llm_app", "rag_app", "workflow", "data_pipeline"}:
        return explicit_type

    artifact_signals = " ".join(
        " ".join(part for part in [artifact.name, artifact.type, artifact.path, artifact.url] if part)
        for artifact in intake.artifacts
    ).lower()
    request_signals = " ".join(
        [
            str(intake.request),
            str(intake.model),
            str(intake.api),
            str(intake.environment),
            str(intake.interfaces),
            str(intake.entry_points),
            str(intake.dimensions),
            str(intake.oracle),
        ]
    ).lower()

    api_indicators = ("openapi", "swagger", "paths", ".json", ".yaml", ".yml")
    model_indicators = (
        "model_endpoint",
        "labels",
        "dataset",
        "evaluation",
        "metric",
        "inference",
        "model",
        "endpoint",
    )
    mobile_indicators = (
        "mobile",
        "android",
        "ios",
        "apk",
        "ipa",
        "bundle",
        "package",
        "deeplink",
        "permission",
        "appium",
        "device",
    )
    llm_app_indicators = (
        "llm",
        "prompt",
        "response",
        "conversation",
        "tool",
        "fallback",
        "safety",
        "rag",
        "guardrail",
        "chat",
    )
    rag_app_indicators = (
        "rag",
        "retrieval",
        "grounding",
        "citation",
        "context",
        "vector",
        "corpus",
        "knowledge",
    )
    workflow_indicators = (
        "workflow",
        "trigger",
        "step",
        "transition",
        "state",
        "orchestration",
        "idempotency",
        "retry",
    )
    data_pipeline_indicators = (
        "pipeline",
        "schema",
        "transform",
        "batch",
        "etl",
        "integrity",
        "dataset",
        "table",
    )
    web_indicators = ("url", "base_url", "feature", "auth", "booking", "page")

    def _score(indicators: tuple[str, ...]) -> int:
        return sum(1 for token in indicators if token in artifact_signals or token in request_signals)

    scores = {
        "api": _score(api_indicators),
        "model": _score(model_indicators),
        "mobile": _score(mobile_indicators),
        "llm_app": _score(llm_app_indicators),
        "rag_app": _score(rag_app_indicators),
        "workflow": _score(workflow_indicators),
        "data_pipeline": _score(data_pipeline_indicators),
        "web": _score(web_indicators),
    }

    if intake.url or intake.feature:
        scores["web"] += 1
    if intake.labels:
        scores["model"] += 1
        scores["llm_app"] += 1

    # Favor mobile and llm_app when explicit platform/application hints exist.
    if scores["mobile"] >= 2:
        return "mobile"
    if scores["rag_app"] >= 2 and scores["rag_app"] >= scores["llm_app"]:
        return "rag_app"
    if scores["workflow"] >= 2 and scores["workflow"] >= scores["web"]:
        return "workflow"
    if scores["data_pipeline"] >= 2 and scores["data_pipeline"] >= scores["api"]:
        return "data_pipeline"
    if scores["llm_app"] >= 2 and scores["llm_app"] >= scores["model"]:
        return "llm_app"
    if scores["api"] >= 1 and scores["api"] >= scores["model"]:
        return "api"
    if scores["model"] >= 1 and scores["model"] >= scores["web"]:
        return "model"
    if scores["web"] >= 1:
        return "web"
    return "web"
