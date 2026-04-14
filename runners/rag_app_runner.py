from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _defect(
    defect_id: str,
    severity: str,
    message: str,
    *,
    category: str = "model",
    reproducibility: str = "deterministic",
    confidence_score: float = 0.9,
    **details: Any,
) -> dict[str, Any]:
    return {
        "id": defect_id,
        "severity": severity,
        "category": category,
        "reproducibility": reproducibility,
        "confidence_score": confidence_score,
        "message": message,
        "details": details,
    }


def _safe_execution_rate(executed_cases: int, planned_cases: int) -> float:
    if planned_cases <= 0:
        return 0.0
    return round(executed_cases / planned_cases, 4)


def _load_json_list(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    candidate = Path(path)
    if not candidate.exists():
        return []
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _grounding_signal(response: str, references: list[str]) -> bool:
    if not references:
        return True
    lower = response.lower()
    return any(ref.lower() in lower for ref in references if ref)


def _hallucination_detected(response: str, references: list[str]) -> bool:
    if not references:
        return False
    lower = response.lower()
    risk_tokens = ["guaranteed", "always", "never fails", "100%"]
    has_risky_claim = any(token in lower for token in risk_tokens)
    has_reference = any(ref.lower() in lower for ref in references if ref)
    return has_risky_claim and not has_reference


def run_rag_app_smoke(
    eval_cases: list[dict[str, Any]],
    corpus_path: str | None,
    require_citations: bool,
    tool_names: list[str],
    fallback_strategy: str,
    evidence_dir: str,
) -> dict[str, Any]:
    logs: list[str] = []
    defects: list[dict[str, Any]] = []
    corpus_items = _load_json_list(corpus_path)
    corpus_refs = [str(item.get("id", "")).strip() for item in corpus_items if isinstance(item, dict)]

    planned_cases = max(len(eval_cases), 1) + 5
    passed = 0
    failed = 0
    blocked = 0
    skipped = 0

    if corpus_items:
        passed += 1
        logs.append(f"Corpus loaded with {len(corpus_items)} records.")
    else:
        blocked += 1
        defects.append(
            _defect(
                "rag.corpus_missing",
                "medium",
                "No retrieval corpus data available.",
                category="data",
            )
        )

    if tool_names:
        passed += 1
        logs.append(f"Retrieval tools configured: {', '.join(tool_names)}")
    else:
        blocked += 1
        defects.append(
            _defect(
                "rag.tools_missing",
                "low",
                "No retrieval tool configured for rag_app.",
                category="functional",
                confidence_score=0.8,
            )
        )

    if fallback_strategy:
        passed += 1
        logs.append(f"Fallback strategy configured: {fallback_strategy}")
    else:
        blocked += 1
        defects.append(
            _defect(
                "rag.fallback_missing",
                "medium",
                "No fallback strategy configured for rag_app.",
                category="functional",
            )
        )

    cases = eval_cases or [{"prompt": "health check", "expected_contains": "answer"}]
    for index, case in enumerate(cases, start=1):
        expected = str(case.get("expected_contains", "")).strip().lower()
        expected_reference = str(case.get("expected_reference", case.get("expected_citation", ""))).strip().lower()
        response = str(case.get("mock_response", case.get("prompt", ""))).lower()
        context_hit = bool(case.get("context_hit", True))

        if not context_hit:
            failed += 1
            defects.append(
                _defect(
                    "rag.context_miss",
                    "high",
                    "Retrieval context grounding signal is missing.",
                    case_index=index,
                    category="model",
                )
            )
            continue

        if expected and expected not in response:
            failed += 1
            defects.append(
                _defect(
                    "rag.expected_missing",
                    "medium",
                    "Expected token not found in rag_app response.",
                    case_index=index,
                    expected_contains=expected,
                )
            )
            continue

        references = [item for item in [expected_reference, *corpus_refs] if item]
        if not _grounding_signal(response, references):
            failed += 1
            defects.append(
                _defect(
                    "rag.grounding_failed",
                    "high",
                    "Response does not appear grounded in known references.",
                    case_index=index,
                    references=references[:5],
                )
            )
            continue

        if _hallucination_detected(response, references):
            failed += 1
            defects.append(
                _defect(
                    "rag.hallucination_risk",
                    "high",
                    "Rule-based hallucination risk detected.",
                    case_index=index,
                    response_snippet=response[:200],
                )
            )
            continue

        if require_citations and expected_reference and expected_reference not in response:
            failed += 1
            defects.append(
                _defect(
                    "rag.citation_missing",
                    "high",
                    "Citation/reference requirement not satisfied in response.",
                    case_index=index,
                    expected_reference=expected_reference,
                )
            )
            continue

        passed += 1
        logs.append(f"Case {index} passed grounding/hallucination checks.")

    total_checks = passed + failed + blocked + skipped
    executed_cases = passed + failed + blocked
    status = "failed" if failed > 0 else "blocked" if blocked > 0 and passed == 0 else "passed"
    requirement_coverage = round(min(1.0, max(0.4, passed / max(planned_cases, 1))), 4)

    trace_file = Path(evidence_dir) / "rag_app_smoke_trace.log"
    trace_file.parent.mkdir(parents=True, exist_ok=True)
    trace_file.write_text("\n".join(logs), encoding="utf-8")

    return {
        "status": status,
        "summary": {
            "total_checks": total_checks,
            "passed": passed,
            "failed": failed,
            "blocked": blocked,
            "skipped": skipped,
        },
        "coverage": {
            "planned_cases": planned_cases,
            "executed_cases": executed_cases,
            "execution_rate": _safe_execution_rate(executed_cases, planned_cases),
            "requirement_coverage": requirement_coverage,
        },
        "defects": defects,
        "evidence": {
            "logs": logs,
            "screenshots": [],
            "traces": [str(trace_file)],
            "artifacts": [str(trace_file)] + ([corpus_path] if corpus_path else []),
        },
        "recommendation_notes": [
            "RAG smoke now checks grounding and rule-based hallucination risk.",
            "Add live retrieval traces and citation evaluators for production gates.",
        ],
        "raw_output": {
            "corpus_path": corpus_path,
            "require_citations": require_citations,
            "tool_names": tool_names,
            "fallback_strategy": fallback_strategy,
            "corpus_reference_count": len(corpus_refs),
        },
    }
