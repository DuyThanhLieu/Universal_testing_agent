# Universal Testing Agent

Universal Testing Agent (`uta`) is a manifest-driven AI testing orchestrator for web apps, APIs, and model endpoints.

## v1.1 Release Highlights

- Runnable CLI flow: `validate-manifest`, `plan`, `run`, `report`
- Orchestrator modules: intake, classifier, planner, router, executor, reporter
- Adapter coverage: web (Playwright), API (pytest), model (custom evaluator)
- Sample manifest included: `manifests/samples/web_booking.yaml`
- Test suite status: `pytest` passing

## v1.2 Release Highlights

- Standardized run-result contract across web/api/model adapters:
  - `run_id`, `project_name`, `project_type`, `adapter`, `status`, timing, `summary`, `coverage`, `defects`, `evidence`, `recommendation`
- Added sample manifests:
  - `manifests/samples/api_verify_store.yaml`
  - `manifests/samples/model_basalt.yaml`
- Improved planner with product-specific output:
  - Web priorities + constraints
  - API endpoint matrix + auth/contract/negative coverage focus
  - Model evaluation dimensions + metrics + threshold notes
- Added lightweight smoke execution hooks that are offline-friendly and deterministic when live systems are unavailable.
- `report` command now outputs both JSON and Markdown (`results/report_latest.md`).
- Expanded CLI integration tests to cover validate/plan/run/report flows for web/api/model manifests.

## v1.3 Release Highlights

- Observability for every CLI command with per-run artifacts in `results/runs/<run_id>/`:
  - `metadata.json`
  - `run.log`
- New policy/rule engine (`orchestrator/policy.py`) evaluating:
  - `blockers_allowed`
  - `critical_allowed`
  - `minimum_coverage`
  - `max_failed`
- New test asset generation (`generate-assets`) with standardized outputs:
  - `results/checklist_latest.json`
  - `results/checklist_latest.md`
  - `results/testcases_latest.json`
  - `results/testcases_latest.md`
  - `results/bug_report_template.md`
- Improved JSON/Markdown reports with:
  - policy evaluation
  - release gate summary
  - known gaps
  - assumptions
  - generated artifact references
- Extended tests for policy engine, asset generation, CLI asset command, run artifact directory creation, and policy-aware report output.

## v1.4 Release Highlights

- Added run history persistence under `results/history/` with indexed records:
  - per-record run summaries
  - `results/history/history_index.json`
- Added trend analytics (`orchestrator/trends.py`):
  - runs analyzed
  - overall/pass-rate/coverage/defect/release-readiness trends
  - outputs:
    - `results/trends_latest.json`
    - `results/trends_latest.md`
- Added contract validation module (`orchestrator/contracts.py`):
  - manifest contract checks by product type
  - result contract basics
  - API OpenAPI-like basics
  - model labels/dataset basics
  - outputs:
    - `results/contract_validation_latest.json`
    - `results/contract_validation_latest.md`
- Added comparison module (`orchestrator/compare.py`) and CLI command:
  - compare passed/failed/coverage/defects/release readiness
  - outputs:
    - `results/compare_latest.json`
    - `results/compare_latest.md`
- Extended report content with trend summary, contract summary, comparison summary, regression signals, and flaky suspicion notes.
- Added CLI commands:
  - `trends`
  - `validate-contract`
  - `compare`

## v1.5 Release Highlights

- Capability-driven orchestration foundation:
  - `orchestrator/capabilities.py` introduces a typed capability model for end-to-end testing workflows.
- Adapter registry:
  - `orchestrator/registry.py` maps product type -> adapter, supported capabilities, and fallback mode.
  - Supported product types now include:
    - `web`
    - `api`
    - `model`
    - `mobile`
    - `llm_app`
- Taxonomy engine:
  - `orchestrator/taxonomy.py` adds deterministic defaults for dimensions, risks, planning priorities, and coverage focus by product type.
  - Planner now uses taxonomy output for strategy generation.
- Manifest v2 draft support:
  - Added `schemas/manifest_v2.yaml`.
  - Intake supports both legacy manifests and v2-style manifests with `project.name/type/subtype`, interfaces, entry points, oracle, baseline, dependencies, and dimensions.
- New skeleton adapters:
  - `adapters/mobile_adapter.py`
  - `adapters/llm_app_adapter.py`
  - Both are deterministic, offline-safe smoke adapters with fallback behavior.
- New sample manifests:
  - `manifests/samples/mobile_app_smoke.yaml`
  - `manifests/samples/llm_app_eval.yaml`
- Reporting improvements:
  - Reports now include capabilities used, taxonomy coverage focus, and fallback execution notes when skeleton modes are active.
- Extended tests for:
  - registry behavior
  - taxonomy behavior
  - manifest v2 compatibility
  - classifier support for `mobile` and `llm_app`
  - new adapter behavior
  - CLI smoke flow for new manifests

## v1.6 Release Highlights

- Plugin-ready architecture:
  - `orchestrator/plugins.py` defines typed adapter plugin metadata and inspection contracts.
  - `orchestrator/plugin_loader.py` adds deterministic plugin discovery and validation.
- Plugin-aware registry/router:
  - built-in and optional local module plugins are supported.
  - validation runs before plugin activation.
  - duplicate/conflict handling is deterministic and introspectable.
- Built-in adapter plugins:
  - `web`, `api`, `model`, `mobile`, `llm_app`
- New CLI introspection commands:
  - `list-plugins`
  - `inspect-plugin <plugin_name>`
- Reports include plugin context:
  - plugin name/version
  - capability path used
  - plugin validation summary
  - fallback execution note
- Extensibility direction prepared for future plugin types:
  - `chatbot`, `rag_app`, `workflow`, `desktop_app`, `browser_extension`, `database`, `data_pipeline`

## v1.7 Release Highlights

- New built-in product plugins and adapters/runners:
  - `rag_app`
  - `workflow`
  - `data_pipeline`
- Added new sample manifests and offline-safe sample artifacts:
  - `manifests/samples/rag_app_eval.yaml`
  - `manifests/samples/workflow_smoke.yaml`
  - `manifests/samples/data_pipeline_validation.yaml`
- Taxonomy and planner expanded for new product types with meaningful defaults for:
  - rag grounding/citation/hallucination risk
  - workflow trigger/transition/recovery/idempotency
  - data-pipeline schema/integrity/transformation/batch handling
- Added plugin onboarding framework:
  - `orchestrator/plugin_onboarding.py`
  - completeness scoring and missing-item visibility per plugin
- Added plugin scaffolding command:
  - `uta scaffold-plugin <product_type> [--mode generic|llm_like|pipeline_like]`
- Added capability/product coverage catalog:
  - `uta coverage-catalog`
  - outputs:
    - `results/coverage_catalog_latest.json`
    - `results/coverage_catalog_latest.md`
- Plugin inspection and list outputs now include:
  - support level (`full`, `partial`, `fallback_only`)
  - missing recommended capabilities
  - onboarding readiness summary
- Reports now include plugin onboarding/support-level context and coverage catalog reference.

## v1.8 Release Highlights

- Execution depth improvements across runners/adapters:
  - `web`: page load, selector checks, navigation checks, optional Playwright probe with deterministic fallback
  - `api`: status code validation, required-field checks, negative cases, auth simulation
  - `model`: offline metrics (`accuracy`, `precision`, `recall`, `f1_score`) from local dataset samples
  - `rag_app`: grounding/reference checks and rule-based hallucination risk detection
  - `data_pipeline`: schema + consistency + batch completeness checks
- Quality gates system:
  - `orchestrator/quality_gates.py`
  - rules supported: `max_critical_defects`, `max_failed_tests`, `minimum_coverage`, `contract_validation_required`, `fallback_not_allowed`
  - gate output: `pass` / `warning` / `fail`, reasons, blocking issues, recommendation
- Plugin packaging and metadata enforcement:
  - plugin metadata now includes `author`, `dependencies`, `compatibility`
  - semantic-version enforcement for plugin versions
  - new commands:
    - `uta export-plugin <plugin_name>`
    - `uta import-plugin <path>`
- CI/CD outputs:
  - `uta report <result.json> --format junit` -> JUnit XML
  - `uta report <result.json> --format ci` -> CI summary JSON
  - `uta evaluate-gates <result.json>` -> explicit quality gate evaluation output
  - exit codes:
    - `0` pass
    - `1` warning
    - `2` fail
- Defect standardization:
  - defect details now include `severity`, `category`, `reproducibility`, `confidence_score`
- Reporting improvements:
  - quality gate section
  - defect detail breakdown
  - capability coverage summary
  - plugin metadata/completeness context

## Requirements

- Python 3.11+
- Playwright browsers installed for web execution (`playwright install`)

## Install

```bash
pip install -e .
```

## Commands

```bash
uta validate-manifest manifests/samples/web_booking.yaml
uta plan manifests/samples/web_booking.yaml
uta generate-assets manifests/samples/web_booking.yaml
uta run manifests/samples/web_booking.yaml
uta report results/latest.json
uta report results/latest.json --format junit
uta report results/latest.json --format ci
uta evaluate-gates results/latest.json
uta trends
uta validate-contract manifests/samples/api_verify_store.yaml
uta compare results/latest.json results/latest.json
uta validate-manifest manifests/samples/mobile_app_smoke.yaml
uta validate-manifest manifests/samples/llm_app_eval.yaml
uta list-plugins
uta inspect-plugin web
uta inspect-plugin rag_app
uta inspect-plugin workflow
uta inspect-plugin data_pipeline
uta plan manifests/samples/rag_app_eval.yaml
uta generate-assets manifests/samples/workflow_smoke.yaml
uta run manifests/samples/data_pipeline_validation.yaml
uta coverage-catalog
uta scaffold-plugin sample_custom_product
uta export-plugin web
uta import-plugin results/plugin_packages/web-1.8.0.json
```

## Project Layout

- `orchestrator/`: intake, classifier, planner, router, executor, reporter
- `adapters/`: pluggable test adapters per product type
- `runners/`: concrete test execution logic
- `schemas/`: YAML schemas for intake/result contracts
- `manifests/samples/`: sample manifests
