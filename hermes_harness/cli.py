from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hermes_harness.config import HarnessConfig, load_config
from hermes_harness.model import ModelError, OllamaClient
from hermes_harness.workflow import analyze, ask, load_catalog, load_scopes


DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "hermes.ai.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hermes-ai", description="Harness AI-DLC local con Ollama.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("doctor", help="Valida harness, skills y Ollama")
    commands.add_parser("skills", help="Lista las skills instaladas")
    commands.add_parser("stages", help="Lista las 33 etapas AI-DLC")
    analysis = commands.add_parser("analyze", help="Analiza un proyecto con el workflow")
    analysis.add_argument("project")
    analysis.add_argument("--scope", choices=("quick", "analysis"), default="quick")
    question = commands.add_parser("ask", help="Pregunta sobre un proyecto usando herramientas")
    question.add_argument("project")
    question.add_argument("question", nargs="+")
    commands.add_parser("run", help="Consola interactiva")
    return parser


def _skills(config: HarnessConfig) -> list[Path]:
    return sorted(config.skills_directory.glob("hermes-*/SKILL.md"), key=lambda path: path.parent.name)


def doctor(config: HarnessConfig) -> int:
    catalog = load_catalog(config)
    scopes = load_scopes(config)
    skill_paths = _skills(config)
    print("Hermes AI-DLC doctor")
    print(f"  Modo: {config.access_mode}")
    print(f"  Raíces: {', '.join(str(item) for item in config.workspace.workspace_roots)}")
    print(f"  Etapas: {len(catalog)} [{'OK' if len(catalog) == 33 else 'REVISAR'}]")
    print(f"  Scopes: {', '.join(scopes)}")
    print(f"  Skills Hermes: {len(skill_paths)}")
    missing = sorted({stage["skill"] for stage in catalog.values()} - {path.parent.name for path in skill_paths})
    print(f"  Skills faltantes: {', '.join(missing) if missing else 'ninguna'}")
    client = OllamaClient(config.provider)
    try:
        models = client.models()
    except ModelError as error:
        print(f"  Ollama: NO DISPONIBLE ({error})")
        print("  Instala Ollama y descarga el modelo antes de ejecutar análisis con IA.")
        return 2
    installed = config.provider.model in models or any(item.split(":")[0] == config.provider.model for item in models)
    print("  Ollama: OK")
    print(f"  Modelo requerido: {config.provider.model} [{'OK' if installed else 'NO INSTALADO'}]")
    print(f"  Modelos locales: {', '.join(models) if models else 'ninguno'}")
    return 0 if not missing and len(catalog) == 33 and installed else 2


def print_skills(config: HarnessConfig) -> None:
    for path in _skills(config):
        print(f"- {path.parent.name}")


def print_stages(config: HarnessConfig) -> None:
    for stage_id, stage in load_catalog(config).items():
        print(f"- {stage_id} [{stage['phase']}] {stage['name']} -> {stage['skill']} ({stage['mode']})")


def interactive(config: HarnessConfig) -> int:
    print("Hermes AI-DLC listo. Harness en modo de solo lectura.")
    print("Comandos: doctor, skills, stages, analizar <proyecto> [quick|analysis], preguntar <proyecto> <pregunta>, salir")
    while True:
        try:
            raw = input("hermes-ai> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not raw:
            continue
        if raw.casefold() in {"salir", "exit", "quit"}:
            return 0
        try:
            if raw.casefold() == "doctor":
                doctor(config)
            elif raw.casefold() == "skills":
                print_skills(config)
            elif raw.casefold() == "stages":
                print_stages(config)
            elif raw.casefold().startswith("analizar "):
                parts = raw.split()
                scope = parts[-1] if parts[-1] in {"quick", "analysis"} else "quick"
                project = " ".join(parts[1:-1] if parts[-1] == scope and len(parts) > 2 else parts[1:])
                result = analyze(config, project, scope)
                print(f"Análisis completo: {result.report}")
            elif raw.casefold().startswith("preguntar "):
                parts = raw.split(maxsplit=2)
                if len(parts) < 3:
                    print("Uso: preguntar <proyecto> <pregunta>")
                else:
                    print(ask(config, parts[1], parts[2]))
            else:
                print("Comando no reconocido.")
        except (ValueError, OSError, ModelError) as error:
            print(f"Error: {error}")


def execute(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
        print(f"Error de configuración: {error}", file=sys.stderr)
        return 2
    command = args.command or "doctor"
    try:
        if command == "doctor":
            return doctor(config)
        if command == "skills":
            print_skills(config)
            return 0
        if command == "stages":
            print_stages(config)
            return 0
        if command == "analyze":
            result = analyze(config, args.project, args.scope)
            print(f"Proyecto: {result.project}")
            print(f"Reporte: {result.report}")
            print(f"Auditoría: {result.run_directory}")
            return 0
        if command == "ask":
            print(ask(config, args.project, " ".join(args.question)))
            return 0
        return interactive(config)
    except (ValueError, OSError, ModelError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


def main() -> int:
    return execute()
