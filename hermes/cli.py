from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hermes.agent import interactive
from hermes.config import HermesConfig, load_config
from hermes.reports import render_project, save_inventory
from hermes.scanner import find_projects, scan


DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "hermes.config.json"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="hermes", description="Organizador local de proyectos en modo seguro.")
    result.add_argument("--config", default=str(DEFAULT_CONFIG), help="Ruta a hermes.config.json")
    commands = result.add_subparsers(dest="command")
    commands.add_parser("doctor", help="Comprueba la configuración y los permisos")
    commands.add_parser("scan", help="Escanea y genera el inventario")
    show = commands.add_parser("show", help="Muestra el diagnóstico de un proyecto")
    show.add_argument("query", nargs="+", help="Nombre o tecnología a buscar")
    commands.add_parser("run", help="Inicia la consola interactiva")
    return result


def doctor(config: HermesConfig) -> int:
    print(f"Configuración: {config.config_path}")
    print(f"Modo: {config.access_mode}")
    valid = True
    for root in config.workspace_roots:
        exists = root.is_dir()
        print(f"Raíz: {root} [{'OK' if exists else 'NO ENCONTRADA'}]")
        valid = valid and exists
    print(f"Reportes: {config.state_directory}")
    print("Mutaciones en proyectos: DESHABILITADAS")
    return 0 if valid else 2


def execute(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
        print(f"Error de configuración: {error}", file=sys.stderr)
        return 2
    command = args.command or "doctor"
    if command == "doctor":
        return doctor(config)

    inventory = scan(config)
    json_path, markdown_path = save_inventory(config, inventory)
    if command == "scan":
        print(f"Proyectos detectados: {len(inventory.projects)}")
        print(f"Inventario JSON: {json_path}")
        print(f"Reporte: {markdown_path}")
        return 0
    if command == "show":
        matches = find_projects(inventory, " ".join(args.query))
        if not matches:
            print("No se encontraron proyectos.", file=sys.stderr)
            return 1
        print("\n\n".join(render_project(project) for project in matches))
        return 0
    if command == "run":
        interactive(inventory)
        return 0
    return 2


def main() -> int:
    return execute()
