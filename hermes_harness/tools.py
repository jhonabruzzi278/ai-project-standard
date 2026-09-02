from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


TEXT_SUFFIXES = {
    ".astro", ".c", ".cpp", ".cs", ".css", ".go", ".h", ".html", ".java",
    ".js", ".json", ".jsx", ".md", ".mjs", ".php", ".py", ".rb", ".rs",
    ".scss", ".sh", ".sql", ".toml", ".ts", ".tsx", ".txt", ".vue", ".xml",
    ".yaml", ".yml",
}
EXCLUDED = {".git", ".next", ".venv", "__pycache__", "build", "coverage", "dist", "node_modules", "vendor"}


class SafeProjectTools:
    def __init__(self, project_root: Path):
        self.root = project_root.resolve()

    def _safe_path(self, value: str) -> Path:
        candidate = (self.root / value).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("La ruta sale del proyecto autorizado")
        return candidate

    @staticmethod
    def _is_secret(path: Path) -> bool:
        name = path.name.casefold()
        allowed = {".env.example", ".env.sample", ".env.template"}
        if name in allowed:
            return False
        return (
            name == ".env" or name.startswith(".env.") or name in {"credentials", "credentials.json", "id_rsa", "id_ed25519"}
            or path.suffix.casefold() in {".key", ".p12", ".pfx", ".pem"}
        )

    def schemas(self) -> list[dict[str, Any]]:
        return [
            self._schema("project_snapshot", "Get a safe structural summary of the authorized project.", {}),
            self._schema("list_files", "List project files with a depth and result limit.", {
                "path": {"type": "string", "description": "Relative directory, default ."},
                "max_depth": {"type": "integer", "description": "1 to 5"},
                "limit": {"type": "integer", "description": "Maximum 300"},
            }),
            self._schema("read_file", "Read one non-secret text file from the project.", {
                "path": {"type": "string", "description": "Relative file path"},
                "max_chars": {"type": "integer", "description": "Maximum 30000"},
            }, required=["path"]),
            self._schema("search_text", "Search literal text in safe source and documentation files.", {
                "query": {"type": "string"},
                "limit": {"type": "integer", "description": "Maximum 100 matches"},
            }, required=["query"]),
            self._schema("git_status", "Read the current Git branch and working tree status.", {}),
        ]

    @staticmethod
    def _schema(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
        parameters: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            parameters["required"] = required
        return {"type": "function", "function": {"name": name, "description": description, "parameters": parameters}}

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        try:
            if name == "project_snapshot":
                result = self.project_snapshot()
            elif name == "list_files":
                result = self.list_files(
                    str(arguments.get("path", ".")),
                    int(arguments.get("max_depth", 3)),
                    int(arguments.get("limit", 200)),
                )
            elif name == "read_file":
                result = self.read_file(str(arguments.get("path", "")), int(arguments.get("max_chars", 20000)))
            elif name == "search_text":
                result = self.search_text(str(arguments.get("query", "")), int(arguments.get("limit", 50)))
            elif name == "git_status":
                result = self.git_status()
            else:
                return json.dumps({"error": f"Herramienta no permitida: {name}"}, ensure_ascii=False)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            return json.dumps({"error": str(error)}, ensure_ascii=False)

    def project_snapshot(self) -> dict[str, Any]:
        try:
            top = sorted(self.root.iterdir(), key=lambda item: item.name.casefold())
        except OSError as error:
            raise ValueError(f"No se puede leer el proyecto: {error}") from error
        manifests = [
            name for name in (
                "package.json", "pyproject.toml", "requirements.txt", "composer.json", "Cargo.toml",
                "go.mod", "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "README.md",
                "PROJECT.yaml", "astro.config.mjs", "next.config.js", "vite.config.ts",
            ) if (self.root / name).exists()
        ]
        return {
            "root": str(self.root),
            "top_level": [item.name + ("/" if item.is_dir() else "") for item in top[:150]],
            "manifests": manifests,
            "secret_files_present": [item.name for item in top if item.is_file() and self._is_secret(item)],
            "note": "Secret values were not read.",
        }

    def list_files(self, relative: str = ".", max_depth: int = 3, limit: int = 200) -> list[str]:
        base = self._safe_path(relative)
        max_depth = max(1, min(max_depth, 5))
        limit = max(1, min(limit, 300))
        if not base.is_dir():
            raise ValueError("La ruta no es un directorio")
        output: list[str] = []
        for current, dirs, files in os.walk(base):
            current_path = Path(current)
            depth = len(current_path.relative_to(base).parts)
            dirs[:] = [name for name in dirs if name not in EXCLUDED and not self._is_secret(current_path / name)]
            if depth >= max_depth:
                dirs[:] = []
            for name in sorted(files, key=str.casefold):
                path = current_path / name
                if self._is_secret(path):
                    continue
                output.append(str(path.relative_to(self.root)))
                if len(output) >= limit:
                    return output
        return output

    def read_file(self, relative: str, max_chars: int = 20000) -> dict[str, Any]:
        path = self._safe_path(relative)
        if self._is_secret(path):
            raise ValueError("Lectura de secretos bloqueada")
        if not path.is_file():
            raise ValueError("El archivo no existe")
        if path.suffix.casefold() not in TEXT_SUFFIXES and path.name not in {"Dockerfile", "Makefile", ".gitignore"}:
            raise ValueError("Tipo de archivo no permitido para lectura")
        max_chars = max(1, min(max_chars, 30000))
        content = path.read_text(encoding="utf-8", errors="replace")
        return {"path": str(path.relative_to(self.root)), "content": content[:max_chars], "truncated": len(content) > max_chars}

    def search_text(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        if not query:
            raise ValueError("La búsqueda está vacía")
        limit = max(1, min(limit, 100))
        needle = query.casefold()
        matches: list[dict[str, Any]] = []
        for relative in self.list_files(".", 5, 300):
            path = self.root / relative
            if path.suffix.casefold() not in TEXT_SUFFIXES or path.stat().st_size > 1_000_000:
                continue
            for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if needle in line.casefold():
                    matches.append({"path": relative, "line": line_number, "text": line.strip()[:300]})
                    if len(matches) >= limit:
                        return matches
        return matches

    def git_status(self) -> dict[str, Any]:
        if not (self.root / ".git").exists():
            return {"is_git_repository": False}
        process = subprocess.run(
            ["git", "-C", str(self.root), "status", "--short", "--branch"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20, check=False,
        )
        return {"is_git_repository": True, "exit_code": process.returncode, "status": process.stdout[:12000], "error": process.stderr[:1000]}
