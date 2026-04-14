from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from orchestrator.models import RunMetadata, utc_now_iso


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _duration_seconds(started_at: str, finished_at: str) -> float:
    return round((_parse_iso(finished_at) - _parse_iso(started_at)).total_seconds(), 4)


class RunObserver:
    def __init__(
        self,
        runs_dir: str | Path,
        command: str,
        *,
        manifest_path: str = "",
        project_name: str = "unknown",
        project_type: str = "unknown",
        run_id: str | None = None,
    ) -> None:
        self.run_id = run_id or uuid4().hex
        self.command = command
        self.project_name = project_name
        self.project_type = project_type
        self.manifest_path = manifest_path
        self.started_at = utc_now_iso()
        self.finished_at = self.started_at
        self.status = "started"
        self.artifact_dir = Path(runs_dir) / self.run_id
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.artifact_dir / "run.log"
        self.metadata_file = self.artifact_dir / "metadata.json"
        self.log(f"run started command={self.command}")

    def update_context(
        self,
        *,
        project_name: str | None = None,
        project_type: str | None = None,
        manifest_path: str | None = None,
    ) -> None:
        if project_name is not None:
            self.project_name = project_name
        if project_type is not None:
            self.project_type = project_type
        if manifest_path is not None:
            self.manifest_path = manifest_path

    def log(self, message: str) -> None:
        timestamp = utc_now_iso()
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(f"{timestamp} {message}\n")

    def finalize(self, status: str) -> RunMetadata:
        self.finished_at = utc_now_iso()
        self.status = status
        metadata = RunMetadata(
            run_id=self.run_id,
            command=self.command,
            project_name=self.project_name,
            project_type=self.project_type,
            manifest_path=self.manifest_path,
            started_at=self.started_at,
            finished_at=self.finished_at,
            duration_seconds=_duration_seconds(self.started_at, self.finished_at),
            status=self.status,
            artifact_dir=str(self.artifact_dir),
        )
        self.metadata_file.write_text(json.dumps(metadata.model_dump(mode="json"), indent=2), encoding="utf-8")
        self.log(f"run finished status={self.status}")
        return metadata
