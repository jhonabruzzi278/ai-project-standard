from __future__ import annotations

import json
from pathlib import Path

from hermes.agent import answer
from hermes.config import load_config
from hermes.scanner import inspect_project, scan


def test_inspect_project_detects_node_and_documentation(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    project.mkdir()
    (project / ".git").mkdir()
    (project / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (project / "README.md").write_text("# Demo\n", encoding="utf-8")
    (project / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    (project / "package.json").write_text(
        json.dumps({"dependencies": {"next": "1", "react": "1"}}), encoding="utf-8"
    )
    record = inspect_project(project)
    assert record.git_branch == "main"
    assert "Node.js" in record.technologies
    assert "Next.js" in record.technologies
    assert record.has_readme is True


def test_scan_and_agent_priorities(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    root.mkdir()
    (root / "alpha").mkdir()
    config_path = tmp_path / "hermes.config.json"
    config_path.write_text(json.dumps({
        "workspace_roots": [str(root)],
        "state_directory": ".hermes",
        "access_mode": "read_only",
    }), encoding="utf-8")
    inventory = scan(load_config(config_path))
    assert len(inventory.projects) == 1
    assert "alpha" in answer(inventory, "prioridades")
