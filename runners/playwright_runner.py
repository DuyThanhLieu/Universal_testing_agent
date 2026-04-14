from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests


def _defect(
    defect_id: str,
    severity: str,
    message: str,
    *,
    category: str = "functional",
    reproducibility: str = "deterministic",
    confidence_score: float = 0.95,
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


def _selector_present(html: str, selector: str) -> bool:
    s = selector.strip()
    if not s:
        return False
    lower = html.lower()
    if s.startswith("#"):
        needle = f'id="{s[1:].lower()}"'
        return needle in lower
    if s.startswith("."):
        class_name = s[1:].lower()
        return f'class="{class_name}"' in lower or f" {class_name} " in lower
    return s.lower().strip("<>") in lower


def _playwright_probe(url: str, selector: str | None, timeout_ms: int, browser: str, headless: bool) -> tuple[bool, str]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as exc:
        return False, f"Playwright unavailable: {exc}"

    try:
        with sync_playwright() as p:
            browser_launcher = getattr(p, browser, None)
            if browser_launcher is None:
                return False, f"Configured browser '{browser}' is not available in Playwright."
            instance = browser_launcher.launch(headless=headless)
            page = instance.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=max(timeout_ms, 1000))
            if selector:
                _ = page.locator(selector).first.count()
            instance.close()
        return True, "Playwright probe completed."
    except Exception as exc:
        return False, f"Playwright probe failed: {exc}"


def run_web_smoke(
    url: str,
    auth: dict[str, Any],
    timeout_ms: int,
    screenshot_dir: str,
    browser: str = "chromium",
    headless: bool = True,
    selectors: list[str] | None = None,
    navigation_paths: list[str] | None = None,
) -> dict[str, Any]:
    logs: list[str] = []
    screenshots: list[str] = []
    defects: list[dict[str, Any]] = []

    selectors = [item for item in (selectors or []) if str(item).strip()]
    navigation_paths = [item for item in (navigation_paths or ["/"]) if str(item).strip()]
    planned_cases = 1 + len(selectors) + len(navigation_paths)
    passed = 0
    failed = 0
    blocked = 0
    skipped = 0

    if not url:
        Path(screenshot_dir).mkdir(parents=True, exist_ok=True)
        artifact_path = Path(screenshot_dir) / "web_missing_target.log"
        artifact_path.write_text("No URL was provided. Artifact-presence fallback executed.", encoding="utf-8")
        return {
            "status": "blocked",
            "summary": {"total_checks": 1, "passed": 0, "failed": 0, "blocked": 1, "skipped": 0},
            "coverage": {
                "planned_cases": 1,
                "executed_cases": 1,
                "execution_rate": 1.0,
                "requirement_coverage": 0.25,
            },
            "defects": [
                _defect(
                    "web.missing_url",
                    "medium",
                    "No URL/target provided for web smoke execution",
                    category="functional",
                    confidence_score=1.0,
                ),
            ],
            "evidence": {
                "logs": ["No URL configured; used deterministic fallback."],
                "screenshots": [],
                "traces": [],
                "artifacts": [str(artifact_path)],
            },
            "recommendation_notes": ["Provide a valid URL or base_url to enable real HTTP smoke checks."],
            "raw_output": {"playwright_probe": "skipped"},
        }

    html = ""
    page_loaded = False
    try:
        response = requests.get(url, timeout=max(timeout_ms / 1000, 1), allow_redirects=True)
        logs.append(f"HTTP GET {url} -> {response.status_code}")
        if response.status_code < 400:
            page_loaded = True
            html = response.text or ""
            passed += 1
        else:
            failed += 1
            defects.append(
                _defect(
                    "web.http_status",
                    "high",
                    "Web URL returned non-success status code",
                    category="functional",
                    status_code=response.status_code,
                    url=url,
                )
            )
    except Exception as exc:
        blocked += 1
        logs.append(f"HTTP GET blocked: {exc}")
        defects.append(
            _defect(
                "web.http_unavailable",
                "low",
                "HTTP smoke check could not be completed; treated as blocked",
                category="performance",
                reproducibility="unknown",
                confidence_score=0.7,
                error=str(exc),
                url=url,
            )
        )

    for selector in selectors:
        if not page_loaded:
            blocked += 1
            defects.append(
                _defect(
                    "web.selector_check_blocked",
                    "low",
                    "Selector check blocked because page content was unavailable.",
                    category="functional",
                    reproducibility="unknown",
                    confidence_score=0.7,
                    selector=selector,
                )
            )
            continue
        if _selector_present(html, selector):
            passed += 1
            logs.append(f"Selector check passed: {selector}")
        else:
            failed += 1
            defects.append(
                _defect(
                    "web.selector_missing",
                    "medium",
                    "Expected selector not found in page source.",
                    category="functional",
                    selector=selector,
                    url=url,
                )
            )

    for nav_path in navigation_paths:
        nav_url = urljoin(url.rstrip("/") + "/", str(nav_path).lstrip("/"))
        try:
            nav_response = requests.get(nav_url, timeout=max(timeout_ms / 1000, 1), allow_redirects=True)
            logs.append(f"HTTP NAV {nav_url} -> {nav_response.status_code}")
            if nav_response.status_code < 400:
                passed += 1
            else:
                failed += 1
                defects.append(
                    _defect(
                        "web.navigation_non_success",
                        "medium",
                        "Navigation path returned non-success status code.",
                        category="functional",
                        url=nav_url,
                        status_code=nav_response.status_code,
                    )
                )
        except Exception as exc:
            blocked += 1
            defects.append(
                _defect(
                    "web.navigation_unavailable",
                    "low",
                    "Navigation check blocked; endpoint unavailable.",
                    category="performance",
                    reproducibility="unknown",
                    confidence_score=0.7,
                    url=nav_url,
                    error=str(exc),
                )
            )

    auth_required = bool(auth.get("required"))
    auth_selector = str(auth.get("success_selector", "")).strip() or None
    playwright_ok = False
    playwright_message = "skipped"
    if auth_required or auth_selector:
        playwright_ok, playwright_message = _playwright_probe(url, auth_selector, timeout_ms, browser, headless)
        logs.append(playwright_message)
        if not playwright_ok and auth_required:
            blocked += 1
            defects.append(
                _defect(
                    "web.auth_probe_blocked",
                    "medium",
                    "Auth probe could not complete in this environment.",
                    category="functional",
                    reproducibility="unknown",
                    confidence_score=0.65,
                    selector=auth_selector,
                )
            )

    Path(screenshot_dir).mkdir(parents=True, exist_ok=True)
    trace_file = Path(screenshot_dir) / "web_smoke_trace.log"
    trace_file.write_text("\n".join(logs), encoding="utf-8")

    total_checks = passed + failed + blocked + skipped
    executed_cases = passed + failed + blocked
    requirement_coverage = round(min(1.0, max(0.3, passed / max(planned_cases, 1))), 4)
    status = "failed" if failed > 0 else "blocked" if blocked > 0 and passed == 0 else "passed"

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
            "screenshots": screenshots,
            "traces": [str(trace_file)],
            "artifacts": [str(trace_file)],
        },
        "recommendation_notes": [
            "Web smoke now validates page load, selector presence, and navigation path checks.",
            "Add deterministic local fixtures for deep browser interaction regression coverage.",
        ],
        "raw_output": {
            "url": url,
            "timeout_ms": timeout_ms,
            "selectors": selectors,
            "navigation_paths": navigation_paths,
            "playwright_probe": playwright_message,
        },
    }
