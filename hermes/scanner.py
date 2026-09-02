from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from hermes.config import HermesConfig


TECH_MARKERS: dict[str, tuple[str, ...]] = {
    "Node.js": ("package.json",),
    "Python": ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile"),
    "PHP": ("composer.json",),
    "WordPress": ("wp-config.php", "wp-content"),
    "Rust": ("Cargo.toml",),
    "Go": ("go.mod",),
    "Docker": ("Dockerfile", "docker-compose.yml", "docker-compose.yaml"),
    "Supabase": ("supabase",),
    "Terraform": ("main.tf", ".terraform"),
}


@dataclass(frozen=True)
class ProjectRecord:
    name: str
    path: str
    last_modified: str
    is_git_repository: bool
    git_branch: str | None
    technologies: list[str]
    has_readme: bool
    has_gitignore: bool
    has_env_example: bool
    has_project_contract: bool
    has_tests: bool
    has_ci: bool
    has_local_env: bool
    health_score: int
    recommendations: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Inventory:
    generated_at: str
    access_mode: str
    roots: list[str]
    projects: list[ProjectRecord]

    def to_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "access_mode": self.access_mode,
            "roots": self.roots,
            "projects": [project.to_dict() for project in self.projects],
        }


def _exists_any(project: Path, names: Iterable[str]) -> bool:
    return any((project / name).exists() for name in names)


def _git_branch(project: Path) -> str | None:
    head = project / ".git" / "HEAD"
    try:
        value = head.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None
    prefix = "ref: refs/heads/"
    return value[len(prefix):] if value.startswith(prefix) else value[:12]


def _technologies(project: Path) -> list[str]:
    detected = [
        technology
        for technology, markers in TECH_MARKERS.items()
        if _exists_any(project, markers)
    ]
    package_json = project / "package.json"
    if package_json.is_file():
        try:
            package = json.loads(package_json.read_text(encoding="utf-8"))
            dependencies = {
                **package.get("dependencies", {}),
                **package.get("devDependencies", {}),
            }
            frameworks = {
                "next": "Next.js",
                "react": "React",
                "vue": "Vue",
                "@angular/core": "Angular",
                "typescript": "TypeScript",
            }
            detected.extend(label for key, label in frameworks.items() if key in dependencies)
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    return sorted(set(detected))


def _has_tests(project: Path) -> bool:
    return _exists_any(project, ("tests", "test", "__tests__", "spec", "pytest.ini"))


def _has_ci(project: Path) -> bool:
    return (project / ".github" / "workflows").is_dir() or (project / ".gitlab-ci.yml").is_file()


def _recommendations(*, is_git: bool, has_readme: bool, has_gitignore: bool,
                     has_env_example: bool, has_contract: bool, has_tests: bool,
                     has_ci: bool, has_local_env: bool) -> list[str]:
    items: list[str] = []
    if not is_git:
        items.append("Definir si debe versionarse con Git o archivarse.")
    if not has_readme:
        items.append("Agregar README con propósito, instalación y operación.")
    if not has_gitignore:
        items.append("Agregar .gitignore adecuado a la tecnología.")
    if has_local_env and not has_env_example:
        items.append("Documentar variables en .env.example sin incluir secretos.")
    if not has_contract:
        items.append("Agregar PROJECT.yaml para registrar propietario, estado y arquitectura.")
    if not has_tests:
        items.append("Definir una estrategia mínima de pruebas.")
    if is_git and not has_ci:
        items.append("Evaluar integración continua para validaciones automáticas.")
    return items


def inspect_project(project: Path) -> ProjectRecord:
    is_git = (project / ".git").exists()
    has_readme = _exists_any(project, ("README.md", "README.MD", "README.txt", "readme.md"))
    has_gitignore = (project / ".gitignore").is_file()
    has_env_example = _exists_any(project, (".env.example", ".env.sample"))
    has_contract = _exists_any(project, ("PROJECT.yaml", "PROJECT.yml"))
    has_tests = _has_tests(project)
    has_ci = _has_ci(project)
    has_local_env = (project / ".env").is_file()
    checks = (is_git, has_readme, has_gitignore, has_env_example, has_contract, has_tests, has_ci)
    modified = datetime.fromtimestamp(project.stat().st_mtime, tz=timezone.utc).isoformat()
    return ProjectRecord(
        name=project.name,
        path=str(project),
        last_modified=modified,
        is_git_repository=is_git,
        git_branch=_git_branch(project) if is_git else None,
        technologies=_technologies(project),
        has_readme=has_readme,
        has_gitignore=has_gitignore,
        has_env_example=has_env_example,
        has_project_contract=has_contract,
        has_tests=has_tests,
        has_ci=has_ci,
        has_local_env=has_local_env,
        health_score=round(100 * sum(checks) / len(checks)),
        recommendations=_recommendations(
            is_git=is_git, has_readme=has_readme, has_gitignore=has_gitignore,
            has_env_example=has_env_example, has_contract=has_contract,
            has_tests=has_tests, has_ci=has_ci, has_local_env=has_local_env,
        ),
    )


def scan(config: HermesConfig) -> Inventory:
    projects: list[ProjectRecord] = []
    for root in config.workspace_roots:
        if not root.is_dir():
            continue
        for project in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
            if project.is_dir() and project.name not in config.exclude_projects:
                projects.append(inspect_project(project))
    return Inventory(
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        access_mode=config.access_mode,
        roots=[str(root) for root in config.workspace_roots],
        projects=projects,
    )


def find_projects(inventory: Inventory, query: str) -> list[ProjectRecord]:
    terms = [term for term in re.split(r"\s+", query.casefold()) if term]
    if not terms:
        return inventory.projects
    return [
        project for project in inventory.projects
        if all(
            term in " ".join([project.name, project.path, *project.technologies]).casefold()
            for term in terms
        )
    ]
