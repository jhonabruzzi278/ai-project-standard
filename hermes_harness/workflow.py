from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hermes_deep.scanner import DeepRecord, scan as deep_scan
from hermes_harness.config import HarnessConfig
from hermes_harness.model import ModelError, OllamaClient
from hermes_harness.state import RunStore
from hermes_harness.tools import SafeProjectTools


@dataclass(frozen=True)
class AnalysisResult:
    project: Path
    scope: str
    report: Path
    run_directory: Path


def load_catalog(config: HarnessConfig) -> dict[str, dict[str, Any]]:
    data = json.loads(config.catalog_path.read_text(encoding="utf-8"))
    return {stage["id"]: stage for stage in data["stages"]}


def load_scopes(config: HarnessConfig) -> dict[str, Any]:
    return json.loads(config.scopes_path.read_text(encoding="utf-8"))


def load_skill(config: HarnessConfig, name: str) -> str:
    path = config.skills_directory / name / "SKILL.md"
    content = path.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return content


def resolve_project(config: HarnessConfig, query: str) -> DeepRecord:
    inventory = deep_scan(config.workspace)
    term = query.casefold().strip()
    exact = [item for item in inventory.projects if term in {item.name.casefold(), item.relative_path.casefold(), item.path.casefold()}]
    matches = exact or [item for item in inventory.projects if term in item.name.casefold() or term in item.relative_path.casefold()]
    if not matches:
        raise ValueError(f"No se encontró un proyecto real para: {query}")
    if len(matches) > 1:
        names = ", ".join(item.relative_path for item in matches[:10])
        raise ValueError(f"La búsqueda es ambigua. Coincidencias: {names}")
    return matches[0]


def _stage_prompt(stage: dict[str, Any], project: DeepRecord, prior: list[str]) -> str:
    prior_text = ", ".join(prior) if prior else "ninguno"
    return f"""Ejecuta la etapa AI-DLC {stage['id']} — {stage['name']} sobre este proyecto existente:

Ruta autorizada: {project.path}
Tecnologías detectadas inicialmente: {', '.join(project.technologies) or 'sin detectar'}
Artefactos previos disponibles en esta ejecución: {prior_text}

Trabaja exclusivamente en modo de análisis y solo lectura. Usa las herramientas para obtener evidencia suficiente; no supongas que el inventario inicial es completo. Responde en español con Markdown.

Incluye:
- resumen ejecutivo de la etapa;
- evidencia con rutas relativas concretas;
- hallazgos confirmados separados de inferencias;
- riesgos o brechas priorizados;
- preguntas abiertas;
- recomendaciones accionables que aún no se han ejecutado.

No incluyas valores secretos ni afirmes haber ejecutado pruebas, builds, despliegues o cambios.
"""


def analyze(config: HarnessConfig, query: str, scope: str, client: OllamaClient | None = None) -> AnalysisResult:
    scopes = load_scopes(config)
    if scope not in {"quick", "analysis"}:
        raise ValueError("El MVP local permite los scopes quick y analysis; full requiere gates de escritura aún no habilitados")
    project = resolve_project(config, query)
    project_path = Path(project.path)
    catalog = load_catalog(config)
    stage_ids = scopes[scope]["stages"]
    model = client or OllamaClient(config.provider)
    store = RunStore(config.state_directory, project_path, scope, config.provider.model)
    tools = SafeProjectTools(project_path)
    core_rules = (config.repository_root / "harness" / "core-rules.md").read_text(encoding="utf-8")
    artifacts: list[Path] = []

    for stage_id in stage_ids:
        stage = catalog[stage_id]
        store.audit("STAGE_STARTED", {"stage": stage_id, "name": stage["name"], "mode": stage["mode"]})
        try:
            if stage["mode"] == "deterministic":
                artifact = store.save_json_artifact(stage["artifact"], {
                    "stage": stage_id,
                    "project": project.to_dict(),
                    "snapshot": tools.project_snapshot(),
                    "access_mode": config.access_mode,
                })
                store.stage_completed(stage_id, artifact, 0)
            else:
                skill = load_skill(config, stage["skill"])
                system = f"{core_rules}\n\n# Active skill\n\n{skill}"
                reply = model.run(
                    system=system,
                    prompt=_stage_prompt(stage, project, [item.name for item in artifacts]),
                    tools=tools,
                )
                artifact = store.save_text_artifact(stage["artifact"], reply.content)
                store.stage_completed(stage_id, artifact, reply.tool_rounds)
            artifacts.append(artifact)
        except (OSError, ValueError, ModelError) as error:
            store.fail(stage_id, str(error))
            raise

    report_lines = [
        f"# Hermes AI-DLC — {project.relative_path}", "",
        f"Scope: `{scope}`  ", f"Modelo: `{config.provider.model}`  ",
        f"Modo: `{config.access_mode}`", "",
        "> Este informe es de solo lectura. No se modificó ni ejecutó el proyecto.", "",
    ]
    for artifact in artifacts:
        if artifact.suffix == ".md":
            report_lines.extend([f"## {artifact.stem.replace('-', ' ').title()}", "", artifact.read_text(encoding="utf-8"), ""])
    report = store.save_text_artifact("REPORT.md", "\n".join(report_lines))
    store.complete(report)
    return AnalysisResult(project=project_path, scope=scope, report=report, run_directory=store.run_directory)


def ask(config: HarnessConfig, query: str, question: str, client: OllamaClient | None = None) -> str:
    project = resolve_project(config, query)
    model = client or OllamaClient(config.provider)
    tools = SafeProjectTools(Path(project.path))
    core_rules = (config.repository_root / "harness" / "core-rules.md").read_text(encoding="utf-8")
    skill = load_skill(config, "hermes-reverse-engineering")
    prompt = f"Proyecto autorizado: {project.path}\n\nPregunta: {question}\n\nResponde en español, usa herramientas y cita rutas relativas. Solo lectura."
    return model.run(system=f"{core_rules}\n\n# Active skill\n\n{skill}", prompt=prompt, tools=tools).content
