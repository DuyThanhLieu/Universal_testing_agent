from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "cli.main", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )


def test_list_plugins_command_outputs_plugin_summary() -> None:
    proc = _run_cli("list-plugins")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "listed"
    plugin_names = [item["plugin_name"] for item in payload["plugins"]]
    assert "web" in plugin_names
    assert "llm_app" in plugin_names
    assert "rag_app" in plugin_names
    assert "workflow" in plugin_names
    assert "data_pipeline" in plugin_names
    assert "capability_coverage_summary" in payload
    assert "onboarding_summary" in payload


def test_inspect_plugin_command_for_web_llm_and_new_plugins() -> None:
    web_proc = _run_cli("inspect-plugin", "web")
    llm_proc = _run_cli("inspect-plugin", "llm_app")
    rag_proc = _run_cli("inspect-plugin", "rag_app")
    workflow_proc = _run_cli("inspect-plugin", "workflow")
    pipeline_proc = _run_cli("inspect-plugin", "data_pipeline")
    assert web_proc.returncode == 0, web_proc.stdout + web_proc.stderr
    assert llm_proc.returncode == 0, llm_proc.stdout + llm_proc.stderr
    assert rag_proc.returncode == 0, rag_proc.stdout + rag_proc.stderr
    assert workflow_proc.returncode == 0, workflow_proc.stdout + workflow_proc.stderr
    assert pipeline_proc.returncode == 0, pipeline_proc.stdout + pipeline_proc.stderr
    web_payload = json.loads(web_proc.stdout)
    llm_payload = json.loads(llm_proc.stdout)
    rag_payload = json.loads(rag_proc.stdout)
    workflow_payload = json.loads(workflow_proc.stdout)
    pipeline_payload = json.loads(pipeline_proc.stdout)
    assert web_payload["plugin_name"] == "web"
    assert llm_payload["plugin_name"] == "llm_app"
    assert rag_payload["plugin_name"] == "rag_app"
    assert workflow_payload["plugin_name"] == "workflow"
    assert pipeline_payload["plugin_name"] == "data_pipeline"
    assert "author" in web_payload
    assert "compatibility" in llm_payload
    assert "validation" in web_payload
    assert "validation" in llm_payload
    assert "onboarding" in rag_payload


def test_coverage_catalog_command_outputs_files_and_entries() -> None:
    proc = _run_cli("coverage-catalog")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "generated"
    assert Path(payload["coverage_catalog_file"]).exists()
    assert Path(payload["coverage_catalog_markdown_file"]).exists()
    plugin_names = [item["plugin_name"] for item in payload["entries"]]
    assert "rag_app" in plugin_names


def test_scaffold_plugin_command_creates_files_and_allows_cleanup() -> None:
    proc = _run_cli("scaffold-plugin", "sample_custom_product", "--mode", "generic")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "scaffolded"
    created_files = [Path(path) for path in payload["created_files"]]
    for file_path in created_files:
        assert file_path.exists()
    # cleanup generated scaffold files to keep repository clean after test run
    for file_path in created_files:
        if file_path.exists():
            file_path.unlink()
