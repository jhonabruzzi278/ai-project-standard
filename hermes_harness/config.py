from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from hermes.config import HermesConfig, load_config as load_workspace_config


@dataclass(frozen=True)
class ProviderConfig:
    base_url: str
    model: str
    context_window: int
    temperature: float
    max_tool_rounds: int
    timeout_seconds: int


@dataclass(frozen=True)
class HarnessConfig:
    config_path: Path
    repository_root: Path
    workspace: HermesConfig
    provider: ProviderConfig
    access_mode: str
    state_directory: Path
    catalog_path: Path
    scopes_path: Path
    skills_directory: Path
    require_approval_for: frozenset[str]


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def load_config(path: str | Path) -> HarnessConfig:
    config_path = Path(path).expanduser().resolve()
    root = config_path.parent
    data = json.loads(config_path.read_text(encoding="utf-8"))
    provider = data["provider"]
    harness = data["harness"]
    access_mode = harness.get("access_mode", "read_only")
    if access_mode != "read_only":
        raise ValueError("Hermes AI v0.3 solo admite access_mode=read_only")
    if provider.get("type") != "ollama":
        raise ValueError("Hermes AI v0.3 solo admite provider.type=ollama")
    return HarnessConfig(
        config_path=config_path,
        repository_root=root,
        workspace=load_workspace_config(_resolve(root, data["workspace_config"])),
        provider=ProviderConfig(
            base_url=provider["base_url"].rstrip("/"),
            model=provider["model"],
            context_window=int(provider.get("context_window", 8192)),
            temperature=float(provider.get("temperature", 0.1)),
            max_tool_rounds=int(provider.get("max_tool_rounds", 8)),
            timeout_seconds=int(provider.get("timeout_seconds", 300)),
        ),
        access_mode=access_mode,
        state_directory=_resolve(root, harness.get("state_directory", ".hermes/harness")),
        catalog_path=_resolve(root, harness["catalog"]),
        scopes_path=_resolve(root, harness["scopes"]),
        skills_directory=_resolve(root, harness["skills_directory"]),
        require_approval_for=frozenset(harness.get("require_approval_for", [])),
    )
