from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return normalized[:50] or "project"


class RunStore:
    def __init__(self, state_root: Path, project: Path, scope: str, model: str):
        digest = hashlib.sha256(str(project.resolve()).casefold().encode("utf-8")).hexdigest()[:10]
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.run_directory = state_root / f"{_slug(project.name)}-{digest}" / "runs" / f"{stamp}-{scope}"
        self.artifacts_directory = self.run_directory / "artifacts"
        self.artifacts_directory.mkdir(parents=True, exist_ok=False)
        self.audit_path = self.run_directory / "audit.jsonl"
        self.state_path = self.run_directory / "state.json"
        self.state: dict[str, Any] = {
            "version": 1,
            "project": str(project.resolve()),
            "scope": scope,
            "model": model,
            "status": "running",
            "started_at": _now(),
            "completed_stages": [],
            "failed_stage": None,
        }
        self._save_state()
        self.audit("RUN_STARTED", {"scope": scope, "model": model})

    def _save_state(self) -> None:
        self.state_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def audit(self, event: str, details: dict[str, Any]) -> None:
        entry = {"timestamp": _now(), "event": event, **details}
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def save_json_artifact(self, name: str, data: dict[str, Any]) -> Path:
        path = self.artifacts_directory / name
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def save_text_artifact(self, name: str, content: str) -> Path:
        path = self.artifacts_directory / name
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        return path

    def stage_completed(self, stage_id: str, artifact: Path, tool_rounds: int) -> None:
        self.state["completed_stages"].append(stage_id)
        self._save_state()
        self.audit("STAGE_COMPLETED", {
            "stage": stage_id,
            "artifact": str(artifact),
            "tool_rounds": tool_rounds,
        })

    def fail(self, stage_id: str, error: str) -> None:
        self.state["status"] = "failed"
        self.state["failed_stage"] = stage_id
        self.state["error"] = error
        self.state["finished_at"] = _now()
        self._save_state()
        self.audit("RUN_FAILED", {"stage": stage_id, "error": error})

    def complete(self, report: Path) -> None:
        self.state["status"] = "completed"
        self.state["report"] = str(report)
        self.state["finished_at"] = _now()
        self._save_state()
        self.audit("RUN_COMPLETED", {"report": str(report)})
