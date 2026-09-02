from __future__ import annotations

import json
from pathlib import Path

from hermes.config import HermesConfig
from hermes.scanner import Inventory, ProjectRecord


def _yes(value: bool) -> str:
    return "sí" if value else "no"


def render_project(project: ProjectRecord) -> str:
    technologies = ", ".join(project.technologies) or "sin detectar"
    lines = [
        f"{project.name} ({project.health_score}/100)",
        f"  Ruta: {project.path}",
        f"  Tecnologías: {technologies}",
        f"  Git: {_yes(project.is_git_repository)}"
        + (f" ({project.git_branch})" if project.git_branch else ""),
        f"  README: {_yes(project.has_readme)} | PROJECT.yaml: {_yes(project.has_project_contract)} | pruebas: {_yes(project.has_tests)} | CI: {_yes(project.has_ci)}",
    ]
    if project.recommendations:
        lines.append("  Próximos pasos:")
        lines.extend(f"    - {item}" for item in project.recommendations)
    return "\n".join(lines)


def render_markdown(inventory: Inventory) -> str:
    lines = [
        "# Inventario Hermes",
        "",
        f"Generado: `{inventory.generated_at}`",
        f"Modo de acceso: `{inventory.access_mode}`",
        f"Proyectos detectados: **{len(inventory.projects)}**",
        "",
        "| Proyecto | Salud | Tecnologías | Git | README | Contrato | Pruebas | CI |",
        "|---|---:|---|:---:|:---:|:---:|:---:|:---:|",
    ]
    for project in inventory.projects:
        technologies = ", ".join(project.technologies) or "—"
        lines.append(
            f"| {project.name} | {project.health_score} | {technologies} | "
            f"{_yes(project.is_git_repository)} | {_yes(project.has_readme)} | "
            f"{_yes(project.has_project_contract)} | {_yes(project.has_tests)} | "
            f"{_yes(project.has_ci)} |"
        )
    lines.extend(["", "## Recomendaciones por proyecto", ""])
    for project in inventory.projects:
        lines.append(f"### {project.name}")
        lines.extend(
            (f"- {item}" for item in project.recommendations)
            if project.recommendations else ["- Sin brechas básicas detectadas."]
        )
        lines.append("")
    return "\n".join(lines)


def save_inventory(config: HermesConfig, inventory: Inventory) -> tuple[Path, Path]:
    reports = config.state_directory / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    json_path = reports / "inventory.json"
    markdown_path = reports / "inventory.md"
    json_path.write_text(
        json.dumps(inventory.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(inventory) + "\n", encoding="utf-8")
    return json_path, markdown_path
