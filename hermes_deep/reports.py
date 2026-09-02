from __future__ import annotations

import json
from pathlib import Path

from hermes.config import HermesConfig
from hermes_deep.scanner import DeepInventory, DeepRecord


KIND_LABELS = {
    "project": "proyecto",
    "container": "contenedor",
    "collection": "colección/material",
    "empty": "carpeta vacía",
    "unreadable": "sin acceso",
}


def render_record(item: DeepRecord) -> str:
    label = KIND_LABELS.get(item.kind, item.kind)
    lines = [f"{item.name} [{label}]", f"  Ruta: {item.path}"]
    if item.kind == "project":
        lines.extend([
            f"  Salud organizativa: {item.health_score}/100",
            f"  Tecnologías: {', '.join(item.technologies) or 'sin detectar'}",
            f"  Git: {'sí (' + item.git_branch + ')' if item.git_branch else 'no'}",
            f"  README: {'sí' if item.has_readme else 'no'} | PROJECT.yaml: {'sí' if item.has_project_contract else 'no'} | pruebas: {'sí' if item.has_tests else 'no'} | CI: {'sí' if item.has_ci else 'no'}",
        ])
    if item.child_projects:
        lines.append("  Subproyectos: " + ", ".join(item.child_projects))
    if item.recommendations:
        lines.append("  Próximos pasos:")
        lines.extend(f"    - {value}" for value in item.recommendations)
    return "\n".join(lines)


def render_markdown(inventory: DeepInventory) -> str:
    counts = {kind: sum(item.kind == kind for item in inventory.records) for kind in KIND_LABELS}
    lines = [
        "# Inventario profundo de Hermes", "",
        f"Generado: `{inventory.generated_at}`", f"Modo: `{inventory.access_mode}`", "",
        f"- Proyectos reales detectados: **{counts['project']}**",
        f"- Carpetas contenedoras: **{counts['container']}**",
        f"- Colecciones o material: **{counts['collection']}**",
        f"- Carpetas vacías: **{counts['empty']}**", "",
        "| Grupo | Proyecto/ruta | Tipo | Salud | Tecnologías |",
        "|---|---|---|---:|---|",
    ]
    for item in inventory.records:
        score = str(item.health_score) if item.health_score is not None else "—"
        lines.append(
            f"| {item.group} | {item.relative_path} | {KIND_LABELS.get(item.kind, item.kind)} | "
            f"{score} | {', '.join(item.technologies) or '—'} |"
        )
    lines.extend(["", "## Diagnóstico", ""])
    for item in inventory.records:
        lines.append(f"### {item.relative_path}")
        lines.append("")
        lines.append("```text")
        lines.append(render_record(item))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def save(config: HermesConfig, inventory: DeepInventory) -> tuple[Path, Path]:
    reports = config.state_directory / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    json_path = reports / "inventory-deep.json"
    md_path = reports / "inventory-deep.md"
    json_path.write_text(json.dumps(inventory.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(inventory) + "\n", encoding="utf-8")
    return json_path, md_path
