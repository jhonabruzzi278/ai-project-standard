# Hermes Agent + AI-DLC pack

Use the verified setup entrypoint:

```powershell
.\setup-hermes-agent-safe.ps1
```

Then start the real Nous Research Hermes Agent from this repository:

```powershell
ollama launch hermes --model qwen3:8b
```

The agent loads `.hermes.md` automatically and discovers all skills under `skills/`, including `/hermes-aidlc-conductor`.

Example:

```text
Usa /hermes-aidlc-conductor para analizar C:\Trabajos\agrofarias con scope analysis. Solo lectura y cita evidencia.
```

`setup-hermes-agent.ps1` is retained only for compatibility with the first prototype. Prefer the `-safe` script because it writes `external_dirs` as a real YAML sequence and verifies skill discovery.
