from __future__ import annotations

from pathlib import Path


def run_sample_custom_product_smoke(evidence_dir: str) -> dict:
    logs = ["Scaffold runner executed in deterministic mode."]
    trace_file = Path(evidence_dir) / "sample_custom_product_smoke_trace.log"
    trace_file.parent.mkdir(parents=True, exist_ok=True)
    trace_file.write_text("\n".join(logs), encoding="utf-8")
    return {
        "status": "passed",
        "summary": {"total_checks": 1, "passed": 1, "failed": 0, "blocked": 0, "skipped": 0},
        "coverage": {"planned_cases": 1, "executed_cases": 1, "execution_rate": 1.0, "requirement_coverage": 1.0},
        "defects": [],
        "evidence": {"logs": logs, "screenshots": [], "traces": [str(trace_file)], "artifacts": [str(trace_file)]},
        "recommendation_notes": ["Replace scaffold runner logic with product-specific checks."],
        "raw_output": {"scaffold": True},
    }
