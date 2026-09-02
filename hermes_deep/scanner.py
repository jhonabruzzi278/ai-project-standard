from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from hermes.config import HermesConfig


PROJECT_FILES = {
    "package.json", "pyproject.toml", "requirements.txt", "setup.py", "Pipfile",
    "composer.json", "Cargo.toml", "go.mod", "wp-config.php", "PROJECT.yaml",
    "PROJECT.yml", "manage.py", "Gemfile",
}
PROJECT_PATTERNS = ("*.sln", "*.csproj")


@dataclass(frozen=True)
class DeepRecord:
    name: str
    path: str
    relative_path: str
    group: str
    kind: str
    technologies: list[str]
    git_branch: str | None
    health_score: int | None
    has_readme: bool
    has_project_contract: bool
    has_tests: bool
    has_ci: bool
    child_projects: list[str]
    recommendations: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DeepInventory:
    generated_at: str
    access_mode: str
    roots: list[str]
    records: list[DeepRecord]

    @property
    def projects(self) -> list[DeepRecord]:
        return [item for item in self.records if item.kind == "project"]

    def to_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "access_mode": self.access_mode,
            "roots": self.roots,
            "records": [item.to_dict() for item in self.records],
        }


def _exists_any(path: Path, names: tuple[str, ...]) -> bool:
    return any((path / name).exists() for name in names)


def is_project_root(path: Path) -> bool:
    if (path / ".git").exists() or any((path / name).exists() for name in PROJECT_FILES):
        return True
    return any(next(path.glob(pattern), None) is not None for pattern in PROJECT_PATTERNS)


def _discover(path: Path, excluded: frozenset[str], depth: int, max_depth: int) -> list[Path]:
    if is_project_root(path):
        return [path]
    if depth >= max_depth:
        return []
    found: list[Path] = []
    try:
        children = sorted(path.iterdir(), key=lambda item: item.name.casefold())
    except OSError:
        return []
    for child in children:
        if child.is_dir() and child.name not in excluded and not child.name.startswith("."):
            found.extend(_discover(child, excluded, depth + 1, max_depth))
    return found


def _git_branch(path: Path) -> str | None:
    try:
        value = (path / ".git" / "HEAD").read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None
    prefix = "ref: refs/heads/"
    return value[len(prefix):] if value.startswith(prefix) else value[:12]


def _package(path: Path) -> dict[str, object]:
    try:
        return json.loads((path / "package.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def _technologies(path: Path) -> list[str]:
    result: set[str] = set()
    markers = {
        "Astro": ("astro.config.mjs", "astro.config.ts"),
        "Docker": ("Dockerfile", "docker-compose.yml", "docker-compose.yaml"),
        "Go": ("go.mod",),
        "PHP": ("composer.json",),
        "Python": ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile"),
        "Rust": ("Cargo.toml",),
        "Supabase": ("supabase",),
        "Terraform": ("main.tf",),
        "WordPress": ("wp-config.php", "wp-content"),
    }
    for label, names in markers.items():
        if any((path / name).exists() for name in names):
            result.add(label)
    package = _package(path)
    if package:
        result.add("Node.js")
        dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
        for key, label in {
            "astro": "Astro", "next": "Next.js", "react": "React", "vue": "Vue",
            "@angular/core": "Angular", "typescript": "TypeScript", "@sanity/client": "Sanity",
            "vitest": "Vitest", "jest": "Jest",
        }.items():
            if key in dependencies:
                result.add(label)
    if next(path.glob("*.csproj"), None) or next(path.glob("*.sln"), None):
        result.add(".NET")
    return sorted(result)


def _has_tests(path: Path, package: dict[str, object]) -> bool:
    if _exists_any(path, ("tests", "test", "__tests__", "spec", "pytest.ini", "vitest.config.ts", "vitest.config.js", "jest.config.js", "jest.config.ts")):
        return True
    scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
    return isinstance(scripts, dict) and "test" in scripts


def inspect_project(path: Path, root: Path, group: str) -> DeepRecord:
    package = _package(path)
    has_git = (path / ".git").exists()
    has_readme = _exists_any(path, ("README.md", "README.MD", "README.txt", "readme.md"))
    has_gitignore = (path / ".gitignore").is_file()
    has_contract = _exists_any(path, ("PROJECT.yaml", "PROJECT.yml"))
    has_tests = _has_tests(path, package)
    has_ci = (path / ".github" / "workflows").is_dir() or (path / ".gitlab-ci.yml").is_file()
    has_env = (path / ".env").is_file()
    env_documented = not has_env or _exists_any(path, (".env.example", ".env.sample"))
    weighted = [
        (has_git, 20), (has_readme, 15), (has_gitignore, 10), (has_contract, 15),
        (has_tests, 20), (has_ci, 10), (env_documented, 10),
    ]
    score = sum(weight for passed, weight in weighted if passed)
    recommendations: list[str] = []
    if not has_git:
        recommendations.append("Definir versionado Git.")
    if not has_readme:
        recommendations.append("Agregar README operativo.")
    if not has_gitignore:
        recommendations.append("Agregar .gitignore.")
    if not has_contract:
        recommendations.append("Agregar PROJECT.yaml.")
    if not has_tests:
        recommendations.append("Definir pruebas automatizadas.")
    if has_git and not has_ci:
        recommendations.append("Evaluar integración continua.")
    if not env_documented:
        recommendations.append("Documentar variables en .env.example sin secretos.")
    return DeepRecord(
        name=path.name,
        path=str(path),
        relative_path=str(path.relative_to(root)),
        group=group,
        kind="project",
        technologies=_technologies(path),
        git_branch=_git_branch(path) if has_git else None,
        health_score=score,
        has_readme=has_readme,
        has_project_contract=has_contract,
        has_tests=has_tests,
        has_ci=has_ci,
        child_projects=[],
        recommendations=recommendations,
    )


def _folder_kind(path: Path) -> str:
    try:
        children = list(path.iterdir())
    except OSError:
        return "unreadable"
    return "empty" if not children else "collection"


def scan(config: HermesConfig, max_depth: int = 3) -> DeepInventory:
    records: list[DeepRecord] = []
    for root in config.workspace_roots:
        if not root.is_dir():
            continue
        for top in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
            if not top.is_dir() or top.name in config.exclude_projects:
                continue
            projects = _discover(top, config.exclude_directories, 0, max_depth)
            if projects:
                for project in projects:
                    records.append(inspect_project(project, root, top.name))
                if projects != [top]:
                    records.append(DeepRecord(
                        name=top.name, path=str(top), relative_path=str(top.relative_to(root)),
                        group=top.name, kind="container", technologies=[], git_branch=None,
                        health_score=None, has_readme=False, has_project_contract=False,
                        has_tests=False, has_ci=False,
                        child_projects=[str(item.relative_to(top)) for item in projects],
                        recommendations=["Gestionar los subproyectos individualmente; no puntuar el contenedor."],
                    ))
            else:
                kind = _folder_kind(top)
                records.append(DeepRecord(
                    name=top.name, path=str(top), relative_path=str(top.relative_to(root)),
                    group=top.name, kind=kind, technologies=[], git_branch=None,
                    health_score=None, has_readme=False, has_project_contract=False,
                    has_tests=False, has_ci=False, child_projects=[],
                    recommendations=[
                        "Revisar si contiene material de apoyo o un proyecto con estructura no reconocida."
                        if kind == "collection" else "Confirmar si la carpeta vacía debe conservarse."
                    ],
                ))
    return DeepInventory(
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        access_mode=config.access_mode,
        roots=[str(root) for root in config.workspace_roots],
        records=records,
    )


def search(inventory: DeepInventory, query: str) -> list[DeepRecord]:
    term = query.casefold().strip()
    return [item for item in inventory.records if term in " ".join(
        [item.name, item.path, item.group, item.kind, *item.technologies]
    ).casefold()]
