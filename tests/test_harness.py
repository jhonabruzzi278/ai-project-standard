from __future__ import annotations

import json
from pathlib import Path

import pytest

from hermes.config import load_config as load_workspace_config
from hermes_harness.config import HarnessConfig, ProviderConfig
from hermes_harness.model import ModelReply
from hermes_harness.tools import SafeProjectTools
from hermes_harness.workflow import analyze, load_catalog


class FakeModel:
    def run(self, *, system: str, prompt: str, tools: SafeProjectTools) -> ModelReply:
        snapshot = tools.project_snapshot()
        assert snapshot["root"]
        assert "Active skill" in system
        return ModelReply(content="# Resultado\n\nEvidencia: `package.json`.", tool_rounds=1)


def make_config(tmp_path: Path) -> HarnessConfig:
    repository = Path(__file__).resolve().parent.parent
    workspace_root = tmp_path / "work"
    project = workspace_root / "demo"
    project.mkdir(parents=True)
    (project / "package.json").write_text(json.dumps({"scripts": {"test": "vitest"}}), encoding="utf-8")
    (project / "README.md").write_text("# Demo\n", encoding="utf-8")
    (project / ".env").write_text("SECRET=do-not-read\n", encoding="utf-8")
    workspace_path = tmp_path / "workspace.json"
    workspace_path.write_text(json.dumps({
        "workspace_roots": [str(workspace_root)],
        "state_directory": str(tmp_path / "legacy-state"),
        "access_mode": "read_only",
        "exclude_directories": [".git", "node_modules", "dist", "build"],
    }), encoding="utf-8")
    return HarnessConfig(
        config_path=tmp_path / "ai.json",
        repository_root=repository,
        workspace=load_workspace_config(workspace_path),
        provider=ProviderConfig(
            base_url="http://127.0.0.1:11434", model="fake", context_window=4096,
            temperature=0.0, max_tool_rounds=2, timeout_seconds=5,
        ),
        access_mode="read_only",
        state_directory=tmp_path / "harness-state",
        catalog_path=repository / "harness" / "aidlc-stage-catalog.json",
        scopes_path=repository / "harness" / "scopes.json",
        skills_directory=repository / "skills",
        require_approval_for=frozenset({"write", "execute", "network"}),
    )


def test_catalog_has_33_unique_stages(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    catalog = load_catalog(config)
    assert len(catalog) == 33
    assert list(catalog)[0] == "0.1"
    assert list(catalog)[-1] == "4.7"


def test_safe_tools_block_secrets_and_path_escape(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    project = config.workspace.workspace_roots[0] / "demo"
    tools = SafeProjectTools(project)
    snapshot = tools.project_snapshot()
    assert ".env" in snapshot["secret_files_present"]
    assert ".env" not in tools.list_files()
    with pytest.raises(ValueError, match="secretos"):
        tools.read_file(".env")
    with pytest.raises(ValueError, match="sale del proyecto"):
        tools.read_file("..\\outside.txt")


def test_quick_workflow_writes_only_harness_state(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    project = config.workspace.workspace_roots[0] / "demo"
    before = sorted(path.relative_to(project) for path in project.rglob("*"))

    result = analyze(config, "demo", "quick", client=FakeModel())

    after = sorted(path.relative_to(project) for path in project.rglob("*"))
    assert before == after
    assert result.report.is_file()
    assert "Resultado" in result.report.read_text(encoding="utf-8")
    state = json.loads((result.run_directory / "state.json").read_text(encoding="utf-8"))
    assert state["status"] == "completed"
    assert state["completed_stages"] == ["0.2", "2.1", "2.6", "3.6"]
