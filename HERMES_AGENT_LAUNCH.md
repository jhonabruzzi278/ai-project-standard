# Launch Hermes Agent

Run the safe one-time setup:

```powershell
.\setup-hermes-agent-safe.ps1
```

Then launch the Nous Research agent with the local model:

```powershell
ollama launch hermes --model qwen3:8b
```

Inside Hermes:

```text
/hermes-aidlc Analiza C:\Trabajos\agrofarias con scope analysis. Solo lectura y cita evidencia.
```

The `hermes-aidlc` skill is the portable standards-compliant conductor. The longer `hermes-aidlc-conductor` name remains as a compatibility alias for the initial build.
