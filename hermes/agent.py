from __future__ import annotations

from hermes.reports import render_project
from hermes.scanner import Inventory, find_projects


HELP = """Comandos disponibles:
  ayuda                 Muestra esta ayuda.
  proyectos             Lista los proyectos y su salud básica.
  buscar <texto>        Busca por nombre, ruta o tecnología.
  revisar <proyecto>    Muestra el diagnóstico de un proyecto.
  prioridades           Lista los proyectos con más brechas.
  salir                  Cierra Hermes.

Hermes está en modo lectura: no cambia tus proyectos.
"""


def answer(inventory: Inventory, question: str) -> str:
    value = question.strip()
    normalized = value.casefold()
    if normalized in {"ayuda", "help", "?"}:
        return HELP
    if normalized in {"proyectos", "listar", "lista"}:
        return "\n".join(
            f"- {project.name}: {project.health_score}/100"
            for project in inventory.projects
        )
    if normalized.startswith("buscar "):
        matches = find_projects(inventory, value[7:])
        return "\n\n".join(render_project(item) for item in matches) or "No encontré coincidencias."
    if normalized.startswith("revisar "):
        matches = find_projects(inventory, value[8:])
        if not matches:
            return "No encontré ese proyecto."
        if len(matches) > 5:
            return "La búsqueda es amplia. Coincidencias: " + ", ".join(item.name for item in matches)
        return "\n\n".join(render_project(item) for item in matches)
    if normalized in {"prioridades", "prioridad", "brechas"}:
        projects = sorted(inventory.projects, key=lambda item: (item.health_score, item.name.casefold()))[:10]
        return "\n".join(
            f"- {item.name}: {item.health_score}/100 ({len(item.recommendations)} acciones)"
            for item in projects
        )
    return "No entendí la consulta. Escribe 'ayuda' para ver los comandos."


def interactive(inventory: Inventory) -> None:
    print("Hermes local listo. Acceso: solo lectura.")
    print("Escribe 'ayuda' para ver los comandos o 'salir' para terminar.")
    while True:
        try:
            question = input("hermes> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if question.strip().casefold() in {"salir", "exit", "quit"}:
            return
        print(answer(inventory, question))
