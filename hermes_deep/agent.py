from __future__ import annotations

from hermes_deep.reports import KIND_LABELS, render_record
from hermes_deep.scanner import DeepInventory, search


HELP = """Comandos:
  proyectos              Lista proyectos reales, incluidos los anidados.
  contenedores           Lista carpetas que agrupan subproyectos.
  colecciones            Lista carpetas de material sin proyecto detectable.
  vacías                 Lista carpetas realmente vacías.
  prioridades            Prioriza solo proyectos reales.
  revisar <texto>        Diagnóstico profundo.
  buscar <texto>         Busca rutas, grupos y tecnologías.
  ayuda | salir
"""


def answer(inventory: DeepInventory, question: str) -> str:
    raw = question.strip()
    value = raw.casefold()
    if value in {"ayuda", "help", "?"}:
        return HELP
    kind_commands = {
        "proyectos": "project", "contenedores": "container",
        "colecciones": "collection", "vacías": "empty", "vacias": "empty",
    }
    if value in kind_commands:
        kind = kind_commands[value]
        items = [item for item in inventory.records if item.kind == kind]
        if kind == "project":
            return "\n".join(f"- {item.relative_path}: {item.health_score}/100" for item in items)
        return "\n".join(f"- {item.relative_path}" for item in items) or "No hay coincidencias."
    if value == "prioridades":
        items = sorted(inventory.projects, key=lambda item: (item.health_score or 0, item.relative_path.casefold()))[:10]
        return "\n".join(
            f"- {item.relative_path}: {item.health_score}/100 ({len(item.recommendations)} acciones)"
            for item in items
        )
    if value.startswith("revisar ") or value.startswith("buscar "):
        query = raw.split(" ", 1)[1]
        items = search(inventory, query)
        return "\n\n".join(render_record(item) for item in items) or "No encontré coincidencias."
    return "No entendí la consulta. Escribe 'ayuda'."


def interactive(inventory: DeepInventory) -> None:
    print("Hermes profundo listo. Acceso: solo lectura.")
    print("Detecta proyectos anidados y clasifica contenedores. Escribe 'ayuda'.")
    while True:
        try:
            question = input("hermes> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if question.strip().casefold() in {"salir", "exit", "quit"}:
            return
        print(answer(inventory, question))
