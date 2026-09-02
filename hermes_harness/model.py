from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from hermes_harness.config import ProviderConfig


class ModelError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelReply:
    content: str
    tool_rounds: int


class OllamaClient:
    def __init__(self, config: ProviderConfig):
        self.config = config

    def _request(self, endpoint: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.config.base_url}{endpoint}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="GET" if payload is None else "POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as error:
            raise ModelError(f"No se pudo conectar con Ollama: {error.reason}") from error
        except (TimeoutError, json.JSONDecodeError) as error:
            raise ModelError(f"Respuesta inválida o tardía de Ollama: {error}") from error

    def models(self) -> list[str]:
        data = self._request("/api/tags")
        return [item.get("name", "") for item in data.get("models", []) if item.get("name")]

    def available(self) -> bool:
        try:
            self.models()
            return True
        except ModelError:
            return False

    def run(self, *, system: str, prompt: str, tools: Any) -> ModelReply:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        schemas = tools.schemas()
        for round_number in range(self.config.max_tool_rounds + 1):
            payload = {
                "model": self.config.model,
                "messages": messages,
                "tools": schemas,
                "stream": False,
                "think": False,
                "options": {
                    "num_ctx": self.config.context_window,
                    "temperature": self.config.temperature,
                },
            }
            response = self._request("/api/chat", payload)
            message = response.get("message", {})
            calls = message.get("tool_calls") or []
            if not calls:
                content = str(message.get("content", "")).strip()
                if not content:
                    raise ModelError("Ollama devolvió una respuesta vacía")
                return ModelReply(content=content, tool_rounds=round_number)
            messages.append(message)
            for call in calls:
                function = call.get("function", {})
                name = str(function.get("name", ""))
                arguments = function.get("arguments", {})
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                result = tools.execute(name, arguments if isinstance(arguments, dict) else {})
                messages.append({"role": "tool", "tool_name": name, "content": result})
        raise ModelError("Ollama excedió el máximo de rondas de herramientas")
