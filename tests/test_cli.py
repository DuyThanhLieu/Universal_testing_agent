from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_MANIFEST = PROJECT_ROOT / "manifests" / "samples" / "web_booking.yaml"
API_MANIFEST = PROJECT_ROOT / "manifests" / "samples" / "api_verify_store.yaml"
MODEL_MANIFEST = PROJECT_ROOT / "manifests" / "samples" / "model_basalt.yaml"
MOBILE_MANIFEST = PROJECT_ROOT / "manifests" / "samples" / "mobile_app_smoke.yaml"
LLM_MANIFEST = PROJECT_ROOT / "manifests" / "samples" / "llm_app_eval.yaml"
RAG_MANIFEST = PROJECT_ROOT / "manifests" / "samples" / "rag_app_eval.yaml"
WORKFLOW_MANIFEST = PROJECT_ROOT / "manifests" / "samples" / "workflow_smoke.yaml"
PIPELINE_MANIFEST = PROJECT_ROOT / "manifests" / "samples" / "data_pipeline_validation.yaml"
RUNS_DIR = PROJECT_ROOT / "results" / "runs"
HISTORY_DIR = PROJECT_ROOT / "results" / "history"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["UTA_TIMEOUT_WEB_MS"] = "200"
    env["UTA_TIMEOUT_API_S"] = "1"
    env["UTA_TIMEOUT_MODEL_S"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "cli.main", *args],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
    )


def _assert_success(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


def _assert_observability_payload(payload: dict) -> None:
    assert payload.get("run_id")
    artifact_dir = payload.get("artifact_dir")
    assert artifact_dir
    metadata = Path(artifact_dir) / "metadata.json"
    run_log = Path(artifact_dir) / "run.log"
    assert metadata.exists()
    assert run_log.exists()


def test_validate_manifest_for_supported_product_samples() -> None:
    web = _assert_success(_run_cli("validate-manifest", str(WEB_MANIFEST)))
    api = _assert_success(_run_cli("validate-manifest", str(API_MANIFEST)))
    model = _assert_success(_run_cli("validate-manifest", str(MODEL_MANIFEST)))
    mobile = _assert_success(_run_cli("validate-manifest", str(MOBILE_MANIFEST)))
    llm = _assert_success(_run_cli("validate-manifest", str(LLM_MANIFEST)))
    rag = _assert_success(_run_cli("validate-manifest", str(RAG_MANIFEST)))
    workflow = _assert_success(_run_cli("validate-manifest", str(WORKFLOW_MANIFEST)))
    pipeline = _assert_success(_run_cli("validate-manifest", str(PIPELINE_MANIFEST)))
    _assert_observability_payload(web)
    _assert_observability_payload(api)
    _assert_observability_payload(model)
    _assert_observability_payload(mobile)
    _assert_observability_payload(llm)
    _assert_observability_payload(rag)
    _assert_observability_payload(workflow)
    _assert_observability_payload(pipeline)


def test_plan_for_supported_product_samples() -> None:
    web = _assert_success(_run_cli("plan", str(WEB_MANIFEST), "--output", "results/plan_web.json"))
    api = _assert_success(_run_cli("plan", str(API_MANIFEST), "--output", "results/plan_api.json"))
    model = _assert_success(_run_cli("plan", str(MODEL_MANIFEST), "--output", "results/plan_model.json"))
    mobile = _assert_success(_run_cli("plan", str(MOBILE_MANIFEST), "--output", "results/plan_mobile.json"))
    llm = _assert_success(_run_cli("plan", str(LLM_MANIFEST), "--output", "results/plan_llm_app.json"))
    rag = _assert_success(_run_cli("plan", str(RAG_MANIFEST), "--output", "results/plan_rag_app.json"))
    _assert_observability_payload(web)
    _assert_observability_payload(api)
    _assert_observability_payload(model)
    _assert_observability_payload(mobile)
    _assert_observability_payload(llm)
    _assert_observability_payload(rag)
    assert (PROJECT_ROOT / "results" / "plan_web.json").exists()
    assert (PROJECT_ROOT / "results" / "plan_api.json").exists()
    assert (PROJECT_ROOT / "results" / "plan_model.json").exists()
    assert (PROJECT_ROOT / "results" / "plan_mobile.json").exists()
    assert (PROJECT_ROOT / "results" / "plan_llm_app.json").exists()
    assert (PROJECT_ROOT / "results" / "plan_rag_app.json").exists()


def test_generate_assets_command_outputs_expected_files() -> None:
    payload = _assert_success(_run_cli("generate-assets", str(WEB_MANIFEST)))
    _assert_observability_payload(payload)
    expected_files = [
        PROJECT_ROOT / "results" / "checklist_latest.json",
        PROJECT_ROOT / "results" / "checklist_latest.md",
        PROJECT_ROOT / "results" / "testcases_latest.json",
        PROJECT_ROOT / "results" / "testcases_latest.md",
        PROJECT_ROOT / "results" / "bug_report_template.md",
    ]
    for file_path in expected_files:
        assert file_path.exists()


def test_generate_assets_for_mobile_and_llm_manifests() -> None:
    mobile_payload = _assert_success(_run_cli("generate-assets", str(MOBILE_MANIFEST)))
    llm_payload = _assert_success(_run_cli("generate-assets", str(LLM_MANIFEST)))
    workflow_payload = _assert_success(_run_cli("generate-assets", str(WORKFLOW_MANIFEST)))
    _assert_observability_payload(mobile_payload)
    _assert_observability_payload(llm_payload)
    _assert_observability_payload(workflow_payload)
    assert any("checklist_latest.json" in path for path in mobile_payload.get("artifacts", []))
    assert any("testcases_latest.json" in path for path in llm_payload.get("artifacts", []))
    assert any("bug_report_template.md" in path for path in workflow_payload.get("artifacts", []))


def test_run_for_web_api_model_and_report_with_policy() -> None:
    web_result = PROJECT_ROOT / "results" / "run_web.json"
    api_result = PROJECT_ROOT / "results" / "run_api.json"
    model_result = PROJECT_ROOT / "results" / "run_model.json"
    json_report = PROJECT_ROOT / "results" / "report_latest.json"
    md_report = PROJECT_ROOT / "results" / "report_latest.md"

    web_payload = _assert_success(_run_cli("run", str(WEB_MANIFEST), "--output", str(web_result)))
    api_payload = _assert_success(_run_cli("run", str(API_MANIFEST), "--output", str(api_result)))
    model_payload = _assert_success(_run_cli("run", str(MODEL_MANIFEST), "--output", str(model_result)))
    _assert_observability_payload(web_payload)
    _assert_observability_payload(api_payload)
    _assert_observability_payload(model_payload)

    assert web_result.exists()
    assert api_result.exists()
    assert model_result.exists()

    report_payload = _assert_success(_run_cli("report", str(model_result), "--output", str(json_report)))
    _assert_observability_payload(report_payload)
    assert json_report.exists()
    assert md_report.exists()
    assert "history_record_file" in report_payload
    assert Path(report_payload["history_record_file"]).exists()

    report_data = json.loads(json_report.read_text(encoding="utf-8"))
    assert "summary" in report_data
    assert "coverage" in report_data
    assert "recommendation" in report_data
    assert "policy" in report_data
    assert "release_gate_summary" in report_data
    assert "artifact_references" in report_data
    assert "capabilities_used" in report_data
    assert "taxonomy_coverage_focus" in report_data


def test_run_and_report_for_mobile_and_llm_manifests() -> None:
    mobile_result = PROJECT_ROOT / "results" / "run_mobile.json"
    llm_result = PROJECT_ROOT / "results" / "run_llm_app.json"
    report_json = PROJECT_ROOT / "results" / "report_llm_app.json"

    mobile_payload = _assert_success(_run_cli("run", str(MOBILE_MANIFEST), "--output", str(mobile_result)))
    llm_payload = _assert_success(_run_cli("run", str(LLM_MANIFEST), "--output", str(llm_result)))
    _assert_observability_payload(mobile_payload)
    _assert_observability_payload(llm_payload)
    assert mobile_result.exists()
    assert llm_result.exists()

    report_payload = _assert_success(_run_cli("report", str(llm_result), "--output", str(report_json)))
    _assert_observability_payload(report_payload)
    assert report_json.exists()


def test_run_and_report_for_data_pipeline_manifest() -> None:
    pipeline_result = PROJECT_ROOT / "results" / "run_data_pipeline.json"
    report_json = PROJECT_ROOT / "results" / "report_data_pipeline.json"
    run_payload = _assert_success(_run_cli("run", str(PIPELINE_MANIFEST), "--output", str(pipeline_result)))
    _assert_observability_payload(run_payload)
    assert pipeline_result.exists()
    assert run_payload.get("plugin_used") == "data_pipeline"

    report_payload = _assert_success(_run_cli("report", str(pipeline_result), "--output", str(report_json)))
    _assert_observability_payload(report_payload)
    assert report_json.exists()
    assert report_payload.get("support_level") in {"full", "partial", "fallback_only", None}


def test_runs_artifact_directory_is_created() -> None:
    payload = _assert_success(_run_cli("validate-manifest", str(WEB_MANIFEST)))
    _assert_observability_payload(payload)
    assert RUNS_DIR.exists()
    assert any(child.is_dir() for child in RUNS_DIR.iterdir())


def test_history_trends_validate_contract_and_compare_commands() -> None:
    run_payload = _assert_success(_run_cli("run", str(API_MANIFEST), "--output", "results/latest.json"))
    _assert_observability_payload(run_payload)
    assert "history_record_file" in run_payload
    assert Path(run_payload["history_record_file"]).exists()
    assert HISTORY_DIR.exists()

    trends_payload = _assert_success(_run_cli("trends"))
    _assert_observability_payload(trends_payload)
    assert (PROJECT_ROOT / "results" / "trends_latest.json").exists()
    assert (PROJECT_ROOT / "results" / "trends_latest.md").exists()
    assert "trends" in trends_payload

    contract_payload = _assert_success(_run_cli("validate-contract", str(API_MANIFEST)))
    _assert_observability_payload(contract_payload)
    assert (PROJECT_ROOT / "results" / "contract_validation_latest.json").exists()
    assert (PROJECT_ROOT / "results" / "contract_validation_latest.md").exists()
    assert "contract_validation" in contract_payload

    compare_payload = _assert_success(_run_cli("compare", "results/latest.json", "results/latest.json"))
    _assert_observability_payload(compare_payload)
    assert (PROJECT_ROOT / "results" / "compare_latest.json").exists()
    assert (PROJECT_ROOT / "results" / "compare_latest.md").exists()
    assert "comparison" in compare_payload


def test_report_supports_junit_and_ci_formats_with_gate_exit_codes() -> None:
    model_result = PROJECT_ROOT / "results" / "run_model_for_ci.json"
    run_payload = _assert_success(_run_cli("run", str(MODEL_MANIFEST), "--output", str(model_result)))
    _assert_observability_payload(run_payload)
    assert model_result.exists()

    junit_proc = _run_cli("report", str(model_result), "--format", "junit")
    assert junit_proc.returncode in {0, 1, 2}, junit_proc.stdout + junit_proc.stderr
    junit_payload = json.loads(junit_proc.stdout)
    assert junit_payload["format"] == "junit"
    assert junit_payload.get("junit_file")
    assert Path(junit_payload["junit_file"]).exists()

    ci_proc = _run_cli("report", str(model_result), "--format", "ci")
    assert ci_proc.returncode in {0, 1, 2}, ci_proc.stdout + ci_proc.stderr
    ci_payload = json.loads(ci_proc.stdout)
    assert ci_payload["format"] == "ci"
    assert ci_payload.get("ci_summary_file")
    assert Path(ci_payload["ci_summary_file"]).exists()


def test_evaluate_gates_and_plugin_packaging_commands() -> None:
    run_payload = _assert_success(_run_cli("run", str(RAG_MANIFEST), "--output", "results/run_rag_for_gates.json"))
    _assert_observability_payload(run_payload)
    result_path = Path("results/run_rag_for_gates.json")
    assert result_path.exists()

    gates_proc = _run_cli("evaluate-gates", str(result_path), "--manifest", str(RAG_MANIFEST))
    assert gates_proc.returncode in {0, 1, 2}, gates_proc.stdout + gates_proc.stderr
    gates_payload = json.loads(gates_proc.stdout)
    assert gates_payload["status"] == "evaluated"
    assert Path(gates_payload["quality_gates_file"]).exists()

    export_proc = _run_cli("export-plugin", "rag_app")
    assert export_proc.returncode == 0, export_proc.stdout + export_proc.stderr
    export_payload = json.loads(export_proc.stdout)
    package_file = Path(export_payload["package_file"])
    assert package_file.exists()

    import_proc = _run_cli("import-plugin", str(package_file))
    assert import_proc.returncode == 0, import_proc.stdout + import_proc.stderr
    import_payload = json.loads(import_proc.stdout)
    assert import_payload["status"] in {"imported", "warning"}
