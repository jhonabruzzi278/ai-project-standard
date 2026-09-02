from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hermes.config import load_config
from hermes_deep.agent import interactive
from hermes_deep.reports import render_record, save
from hermes_deep.scanner import scan, search


DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "hermes.config.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hermes-deep", description="Inventario jerárquico de proyectos.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("scan")
    show = commands.add_parser("show")
    show.add_argument("query", nargs="+")
    commands.add_parser("run")
    return parser


def execute(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
        print(f"Error de configuración: {error}", file=sys.stderr)
        return 2
    inventory = scan(config)
    json_path, md_path = save(config, inventory)
    if (args.command or "scan") == "scan":
        print(f"Proyectos reales: {len(inventory.projects)}")
        print(f"Entidades clasificadas: {len(inventory.records)}")
        print(f"Reporte: {md_path}")
        print(f"Datos: {json_path}")
        return 0
    if args.command == "show":
        items = search(inventory, " ".join(args.query))
        print("\n\n".join(render_record(item) for item in items) or "No se encontraron coincidencias.")
        return 0 if items else 1
    interactive(inventory)
    return 0


def main() -> int:
    return execute()
