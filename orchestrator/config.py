from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class PathSettings(BaseModel):
    results_dir: str = "results"
    runs_dir: str = "results/runs"
    evidence_dir: str = "evidence"
    latest_result_file: str = "results/latest.json"
    latest_plan_file: str = "results/plan_latest.json"
    latest_report_file: str = "results/report_latest.json"
    latest_report_markdown_file: str = "results/report_latest.md"
    latest_junit_file: str = "results/report_latest.junit.xml"
    latest_ci_summary_file: str = "results/ci_summary_latest.json"
    latest_quality_gates_file: str = "results/quality_gates_latest.json"
    latest_checklist_file: str = "results/checklist_latest.json"
    latest_checklist_markdown_file: str = "results/checklist_latest.md"
    latest_testcases_file: str = "results/testcases_latest.json"
    latest_testcases_markdown_file: str = "results/testcases_latest.md"
    latest_bug_report_template_file: str = "results/bug_report_template.md"
    latest_generated_assets_index_file: str = "results/generated_assets_latest.json"
    history_dir: str = "results/history"
    history_index_file: str = "results/history/history_index.json"
    latest_trends_file: str = "results/trends_latest.json"
    latest_trends_markdown_file: str = "results/trends_latest.md"
    latest_contract_validation_file: str = "results/contract_validation_latest.json"
    latest_contract_validation_markdown_file: str = "results/contract_validation_latest.md"
    latest_compare_file: str = "results/compare_latest.json"
    latest_compare_markdown_file: str = "results/compare_latest.md"
    latest_coverage_catalog_file: str = "results/coverage_catalog_latest.json"
    latest_coverage_catalog_markdown_file: str = "results/coverage_catalog_latest.md"
    latest_plugin_packages_dir: str = "results/plugin_packages"
    latest_imported_plugins_dir: str = "results/imported_plugins"


class TimeoutSettings(BaseModel):
    web_ms: int = 8000
    api_s: int = 10
    model_s: int = 20


class WebRunnerSettings(BaseModel):
    browser: str = "chromium"
    headless: bool = True


class ApiRunnerSettings(BaseModel):
    pytest_args: list[str] = Field(default_factory=lambda: ["-q", "--disable-warnings", "--maxfail=1"])


class ModelRunnerSettings(BaseModel):
    default_threshold: float = 0.7


class RunnerSettings(BaseModel):
    web: WebRunnerSettings = Field(default_factory=WebRunnerSettings)
    api: ApiRunnerSettings = Field(default_factory=ApiRunnerSettings)
    model: ModelRunnerSettings = Field(default_factory=ModelRunnerSettings)


class RuntimeConfig(BaseModel):
    paths: PathSettings = Field(default_factory=PathSettings)
    timeouts: TimeoutSettings = Field(default_factory=TimeoutSettings)
    runners: RunnerSettings = Field(default_factory=RunnerSettings)


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return data


def load_runtime_config(config_path: str | Path | None = None) -> RuntimeConfig:
    resolved_path = Path(config_path or os.getenv("UTA_CONFIG_PATH", "configs/default.yaml"))
    config = RuntimeConfig.model_validate(_read_yaml(resolved_path))

    if value := os.getenv("UTA_RESULTS_FILE"):
        config.paths.latest_result_file = value
    if value := os.getenv("UTA_RUNS_DIR"):
        config.paths.runs_dir = value
    if value := os.getenv("UTA_PLAN_FILE"):
        config.paths.latest_plan_file = value
    if value := os.getenv("UTA_REPORT_FILE"):
        config.paths.latest_report_file = value
    if value := os.getenv("UTA_REPORT_MD_FILE"):
        config.paths.latest_report_markdown_file = value
    if value := os.getenv("UTA_JUNIT_FILE"):
        config.paths.latest_junit_file = value
    if value := os.getenv("UTA_CI_SUMMARY_FILE"):
        config.paths.latest_ci_summary_file = value
    if value := os.getenv("UTA_QUALITY_GATES_FILE"):
        config.paths.latest_quality_gates_file = value
    if value := os.getenv("UTA_CHECKLIST_FILE"):
        config.paths.latest_checklist_file = value
    if value := os.getenv("UTA_CHECKLIST_MD_FILE"):
        config.paths.latest_checklist_markdown_file = value
    if value := os.getenv("UTA_TESTCASES_FILE"):
        config.paths.latest_testcases_file = value
    if value := os.getenv("UTA_TESTCASES_MD_FILE"):
        config.paths.latest_testcases_markdown_file = value
    if value := os.getenv("UTA_BUG_TEMPLATE_FILE"):
        config.paths.latest_bug_report_template_file = value
    if value := os.getenv("UTA_GENERATED_ASSETS_INDEX_FILE"):
        config.paths.latest_generated_assets_index_file = value
    if value := os.getenv("UTA_HISTORY_DIR"):
        config.paths.history_dir = value
    if value := os.getenv("UTA_HISTORY_INDEX_FILE"):
        config.paths.history_index_file = value
    if value := os.getenv("UTA_TRENDS_FILE"):
        config.paths.latest_trends_file = value
    if value := os.getenv("UTA_TRENDS_MD_FILE"):
        config.paths.latest_trends_markdown_file = value
    if value := os.getenv("UTA_CONTRACT_VALIDATION_FILE"):
        config.paths.latest_contract_validation_file = value
    if value := os.getenv("UTA_CONTRACT_VALIDATION_MD_FILE"):
        config.paths.latest_contract_validation_markdown_file = value
    if value := os.getenv("UTA_COMPARE_FILE"):
        config.paths.latest_compare_file = value
    if value := os.getenv("UTA_COMPARE_MD_FILE"):
        config.paths.latest_compare_markdown_file = value
    if value := os.getenv("UTA_COVERAGE_CATALOG_FILE"):
        config.paths.latest_coverage_catalog_file = value
    if value := os.getenv("UTA_COVERAGE_CATALOG_MD_FILE"):
        config.paths.latest_coverage_catalog_markdown_file = value
    if value := os.getenv("UTA_PLUGIN_PACKAGES_DIR"):
        config.paths.latest_plugin_packages_dir = value
    if value := os.getenv("UTA_IMPORTED_PLUGINS_DIR"):
        config.paths.latest_imported_plugins_dir = value
    if value := os.getenv("UTA_EVIDENCE_DIR"):
        config.paths.evidence_dir = value
    if value := os.getenv("UTA_TIMEOUT_WEB_MS"):
        config.timeouts.web_ms = int(value)
    if value := os.getenv("UTA_TIMEOUT_API_S"):
        config.timeouts.api_s = int(value)
    if value := os.getenv("UTA_TIMEOUT_MODEL_S"):
        config.timeouts.model_s = int(value)

    return config


def ensure_runtime_dirs(config: RuntimeConfig) -> None:
    Path(config.paths.results_dir).mkdir(parents=True, exist_ok=True)
    Path(config.paths.runs_dir).mkdir(parents=True, exist_ok=True)
    Path(config.paths.evidence_dir).mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_result_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_plan_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_report_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_report_markdown_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_junit_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_ci_summary_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_quality_gates_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_checklist_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_checklist_markdown_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_testcases_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_testcases_markdown_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_bug_report_template_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_generated_assets_index_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.history_dir).mkdir(parents=True, exist_ok=True)
    Path(config.paths.history_index_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_trends_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_trends_markdown_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_contract_validation_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_contract_validation_markdown_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_compare_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_compare_markdown_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_coverage_catalog_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_coverage_catalog_markdown_file).parent.mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_plugin_packages_dir).mkdir(parents=True, exist_ok=True)
    Path(config.paths.latest_imported_plugins_dir).mkdir(parents=True, exist_ok=True)
