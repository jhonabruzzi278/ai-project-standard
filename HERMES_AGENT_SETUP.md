# Use this pack with Nous Research Hermes Agent

Hermes Agent is the runtime. This repository supplies the deterministic AI-DLC stage catalog, safety rules, read-only analyzer, and specialized skills.

## One-time setup

From PowerShell in this repository:

```powershell
.\setup-hermes-agent.ps1
```

The setup script adds this repository's `skills` directory to Hermes Agent's `skills.external_dirs` setting. It does not copy or overwrite the skill sources.

## Start Hermes Agent here

```powershell
ollama launch hermes
```

Hermes Agent will discover `.hermes.md` as project context and expose the skills as slash commands, including `/hermes-aidlc-conductor`.

Ask it, for example:

```text
Usa /hermes-aidlc-conductor para analizar C:\Trabajos\agrofarias en modo analysis. Solo lectura.
```

The legacy `hermes-ai.ps1` remains available as a restricted deterministic runner and local Ollama smoke-test path.
