from __future__ import annotations

import json
from pathlib import Path

from hermes.config import load_config
from hermes_deep.agent import answer
from hermes_deep.scanner import scan


def test_discovers_nested_project_and_classifies_container(tmp_path: Path) -> None:
    root = tmp_path / "work"
    nested = root / "client" / "web"
    nested.mkdir(parents=True)
    (nested / ".git").mkdir()
    (nested / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (nested / "README.md").write_text("# Web\n", encoding="utf-8")
    (nested / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    (nested / "package.json").write_text(json.dumps({
        "scripts": {"test": "vitest"},
        "dependencies": {"astro": "1", "typescript": "1"},
        "devDependencies": {"vitest": "1"},
    }), encoding="utf-8")
    (nested / ".github" / "workflows").mkdir(parents=True)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "workspace_roots": [str(root)],
        "state_directory": ".state",
        "access_mode": "read_only",
        "exclude_directories": ["node_modules", ".git", "dist"],
    }), encoding="utf-8")

    inventory = scan(load_config(config_path))

    assert len(inventory.projects) == 1
    assert inventory.projects[0].relative_path == str(Path("client") / "web")
    assert "Astro" in inventory.projects[0].technologies
    assert any(item.kind == "container" and item.name == "client" for item in inventory.records)
    assert "client" in answer(inventory, "revisar client")


def test_empty_folder_is_not_scored_as_project(tmp_path: Path) -> None:
    root = tmp_path / "work"
    (root / "empty").mkdir(parents=True)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "workspace_roots": [str(root)],
        "state_directory": ".state",
        "access_mode": "read_only",
    }), encoding="utf-8")

    inventory = scan(load_config(config_path))

    assert inventory.records[0].kind == "empty"
    assert inventory.records[0].health_score is None
