from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from orchestrator.intake import load_manifest
from orchestrator.models import ContractValidationResult


REQUIRED_RESULT_FIELDS = {
    "run_id",
    "project_name",
    "project_type",
    "adapter",
    "status",
    "started_at",
    "finished_at",
    "duration_seconds",
    "summary",
    "coverage",
    "defects",
    "defect_details",
    "evidence",
    "recommendation",
    "quality_gates",
}


def _validate_api_artifacts(manifest_artifacts: list[dict[str, Any]]) -> tuple[bool, str]:
    for artifact in manifest_artifacts:
        signal = " ".join(str(artifact.get(key, "")) for key in ("name", "type", "path", "url")).lower()
        if any(token in signal for token in ("openapi", "swagger", "paths")):
            path = artifact.get("path")
            if path and Path(path).exists():
                try:
                    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
                except Exception:
                    return False, f"Failed to parse OpenAPI-like file: {path}"
                if isinstance(payload, dict) and ("paths" in payload or "openapi" in payload or "swagger" in payload):
                    return True, f"OpenAPI-like artifact validated: {path}"
                return False, f"OpenAPI-like artifact missing expected keys: {path}"
            return True, "OpenAPI-like artifact reference detected"
    return False, "No OpenAPI/Swagger artifact found for API project"


def _validate_model_artifacts(labels: list[str], artifacts: list[dict[str, Any]]) -> tuple[bool, str]:
    has_dataset = False
    for artifact in artifacts:
        signal = " ".join(str(artifact.get(key, "")) for key in ("name", "type", "path")).lower()
        if any(token in signal for token in ("dataset", "sample")):
            has_dataset = True
    if labels and has_dataset:
        return True, "Labels and dataset/sample artifact metadata are present"
    if not labels:
        return False, "Model labels are missing"
    return False, "Model dataset/sample artifact is missing"


def _validate_mobile_contract(manifest: Any) -> tuple[bool, str]:
    app_id = manifest.request.get("app_id") or manifest.environment.get("app_id")
    has_mobile_artifact = any(
        any(token in " ".join(str(artifact.get(key, "")) for key in ("name", "type", "path")).lower() for token in ("apk", "ipa", "mobile", "android", "ios"))
        for artifact in [item.model_dump(mode="json") for item in manifest.artifacts]
    )
    has_entry_points = bool(manifest.entry_points or manifest.request.get("entry_points"))
    if app_id or has_mobile_artifact:
        if has_entry_points:
            return True, "Mobile app identifiers/artifacts and entry points are present"
        return True, "Mobile app identifier/artifact detected (entry points optional in skeleton mode)"
    return False, "Missing mobile app_id or mobile artifact hints"


def _validate_llm_app_contract(manifest: Any) -> tuple[bool, str]:
    has_eval_cases = bool(manifest.request.get("eval_cases"))
    has_tools_or_fallback = bool(manifest.request.get("tools")) or bool(manifest.request.get("fallback_strategy"))
    has_dataset = any(
        "dataset" in " ".join(str(artifact.get(key, "")) for key in ("name", "type", "path")).lower()
        for artifact in [item.model_dump(mode="json") for item in manifest.artifacts]
    )
    if has_eval_cases and has_tools_or_fallback and (has_dataset or bool(manifest.labels)):
        return True, "llm_app eval cases, safety/tool/fallback, and dataset/labels signals are present"
    return False, "llm_app contract missing eval cases or safety/tool/fallback or dataset/labels signals"


def _validate_rag_app_contract(manifest: Any) -> tuple[bool, str]:
    has_eval_cases = bool(manifest.request.get("eval_cases"))
    has_retrieval_signal = bool(manifest.request.get("corpus_path")) or any(
        "corpus" in " ".join(str(artifact.get(key, "")) for key in ("name", "type", "path")).lower()
        or "retrieval" in " ".join(str(artifact.get(key, "")) for key in ("name", "type", "path")).lower()
        for artifact in [item.model_dump(mode="json") for item in manifest.artifacts]
    )
    if has_eval_cases and has_retrieval_signal:
        return True, "rag_app contract includes eval cases and retrieval corpus signals"
    return False, "rag_app contract missing eval cases or retrieval corpus signals"


def _validate_workflow_contract(manifest: Any) -> tuple[bool, str]:
    has_steps = bool(manifest.request.get("steps"))
    has_trigger = bool(manifest.request.get("trigger_payload"))
    if has_steps and has_trigger:
        return True, "workflow contract includes trigger payload and step chain"
    return False, "workflow contract missing trigger payload or step definitions"


def _validate_data_pipeline_contract(manifest: Any) -> tuple[bool, str]:
    has_schema = bool(manifest.request.get("schema_path")) or any(
        "schema" in " ".join(str(artifact.get(key, "")) for key in ("name", "type", "path")).lower()
        for artifact in [item.model_dump(mode="json") for item in manifest.artifacts]
    )
    has_batch = bool(manifest.request.get("batch_path")) or any(
        "batch" in " ".join(str(artifact.get(key, "")) for key in ("name", "type", "path")).lower()
        for artifact in [item.model_dump(mode="json") for item in manifest.artifacts]
    )
    if has_schema and has_batch:
        return True, "data_pipeline contract includes schema and batch signals"
    return False, "data_pipeline contract missing schema or batch signals"


def validate_contracts(
    manifest_path: str | Path,
    result_path: str | Path | None = None,
    *,
    check_result_contract: bool = True,
) -> ContractValidationResult:
    manifest = load_manifest(manifest_path)
    checks: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []

    checks["manifest_required_sections"] = {"passed": True, "details": "Manifest parsed and required sections loaded"}

    if manifest.project_type == "api":
        passed, details = _validate_api_artifacts([item.model_dump(mode="json") for item in manifest.artifacts])
        checks["api_contract_basics"] = {"passed": passed, "details": details}
        if not passed:
            reasons.append(details)
    elif manifest.project_type == "model":
        passed, details = _validate_model_artifacts(
            labels=manifest.labels,
            artifacts=[item.model_dump(mode="json") for item in manifest.artifacts],
        )
        checks["model_contract_basics"] = {"passed": passed, "details": details}
        if not passed:
            reasons.append(details)
    elif manifest.project_type == "mobile":
        passed, details = _validate_mobile_contract(manifest)
        checks["mobile_contract_basics"] = {"passed": passed, "details": details}
        if not passed:
            reasons.append(details)
    elif manifest.project_type == "llm_app":
        passed, details = _validate_llm_app_contract(manifest)
        checks["llm_app_contract_basics"] = {"passed": passed, "details": details}
        if not passed:
            reasons.append(details)
    elif manifest.project_type == "rag_app":
        passed, details = _validate_rag_app_contract(manifest)
        checks["rag_app_contract_basics"] = {"passed": passed, "details": details}
        if not passed:
            reasons.append(details)
    elif manifest.project_type == "workflow":
        passed, details = _validate_workflow_contract(manifest)
        checks["workflow_contract_basics"] = {"passed": passed, "details": details}
        if not passed:
            reasons.append(details)
    elif manifest.project_type == "data_pipeline":
        passed, details = _validate_data_pipeline_contract(manifest)
        checks["data_pipeline_contract_basics"] = {"passed": passed, "details": details}
        if not passed:
            reasons.append(details)
    else:
        has_web_target = bool(manifest.url or manifest.environment.get("base_url") or manifest.feature)
        checks["web_contract_basics"] = {
            "passed": has_web_target,
            "details": "Web target indicators present" if has_web_target else "Missing URL/base_url/feature indicators",
        }
        if not has_web_target:
            reasons.append("Missing URL/base_url/feature indicators")

    resolved_result_path = Path(result_path) if result_path else Path("results/latest.json")
    if not check_result_contract:
        checks["result_contract_basics"] = {"passed": True, "details": "Runtime result contract check skipped"}
    elif resolved_result_path.exists():
        try:
            result_payload = json.loads(resolved_result_path.read_text(encoding="utf-8"))
            missing = sorted(REQUIRED_RESULT_FIELDS - set(result_payload.keys()))
            passed = len(missing) == 0
            checks["result_contract_basics"] = {
                "passed": passed,
                "details": "Result contains required fields" if passed else f"Missing fields: {', '.join(missing)}",
            }
            if not passed:
                reasons.append(f"Result contract missing fields: {', '.join(missing)}")
        except Exception as exc:
            checks["result_contract_basics"] = {"passed": False, "details": f"Failed to parse result: {exc}"}
            reasons.append(f"Failed to parse result file: {resolved_result_path}")
    else:
        checks["result_contract_basics"] = {"passed": True, "details": "No result file provided; runtime contract skipped"}

    release_ready = all(item["passed"] for item in checks.values())
    verdict = "pass" if release_ready else "fail"
    return ContractValidationResult(
        release_ready=release_ready,
        verdict=verdict,
        checks=checks,
        reasons=reasons,
    )


def render_contract_validation_markdown(result: ContractValidationResult) -> str:
    lines = [
        "# Contract Validation",
        "",
        f"- Verdict: `{result.verdict}`",
        f"- Release Ready: `{result.release_ready}`",
        "",
        "## Checks",
    ]
    for name, check in result.checks.items():
        status = "PASS" if check.get("passed") else "FAIL"
        lines.append(f"- {name}: `{status}` - {check.get('details', '')}")
    lines.append("")
    lines.append("## Reasons")
    if result.reasons:
        lines.extend([f"- {reason}" for reason in result.reasons])
    else:
        lines.append("- (none)")
    lines.append("")
    return "\n".join(lines)


def save_contract_validation(
    result: ContractValidationResult,
    output_json: str | Path,
    output_md: str | Path,
) -> tuple[Path, Path]:
    json_path = Path(output_json)
    md_path = Path(output_md)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result.model_dump(mode="json"), indent=2), encoding="utf-8")
    md_path.write_text(render_contract_validation_markdown(result), encoding="utf-8")
    return json_path, md_path
