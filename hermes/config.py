from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HermesConfig:
    config_path: Path
    workspace_roots: tuple[Path, ...]
    state_directory: Path
    access_mode: str
    exclude_projects: frozenset[str]
    exclude_directories: frozenset[str]


def load_config(path: str | Path) -> HermesConfig:
    config_path = Path(path).expanduser().resolve()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    roots = tuple(Path(value).expanduser().resolve() for value in data["workspace_roots"])
    if not roots:
        raise ValueError("workspace_roots debe contener al menos una carpeta")

    access_mode = data.get("access_mode", "read_only")
    if access_mode != "read_only":
        raise ValueError("Este MVP solo admite access_mode=read_only")

    state_value = Path(data.get("state_directory", ".hermes"))
    state_directory = (
        state_value.resolve()
        if state_value.is_absolute()
        else (config_path.parent / state_value).resolve()
    )
    return HermesConfig(
        config_path=config_path,
        workspace_roots=roots,
        state_directory=state_directory,
        access_mode=access_mode,
        exclude_projects=frozenset(data.get("exclude_projects", [])),
        exclude_directories=frozenset(data.get("exclude_directories", [])),
    )
