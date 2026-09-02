# Hermes AI-DLC Harness

Hermes combina un orquestador determinista, las cinco fases y 33 etapas de AI-DLC 2.0, skills especializadas, herramientas locales seguras y un modelo servido por Ollama.

La implementación está inspirada en [AWS Labs AI-DLC Workflows](https://github.com/awslabs/aidlc-workflows). No es una distribución oficial de AWS.

## Seguridad inicial

- Los proyectos bajo `C:\Trabajos` son de solo lectura.
- El modelo solo recibe herramientas para inventario, listado, lectura segura, búsqueda y estado Git.
- La lectura de `.env`, claves y credenciales está bloqueada.
- Los artefactos y la auditoría se guardan en `.hermes/harness`.
- Construcción, comandos, red y operación requieren gates que todavía permanecen deshabilitados.

## Comandos

```powershell
.\hermes-ai.ps1 doctor
.\hermes-ai.ps1 skills
.\hermes-ai.ps1 stages
.\hermes-ai.ps1 analyze nexora --scope quick
.\hermes-ai.ps1 analyze agrofarias --scope analysis
.\hermes-ai.ps1 ask nexora "Explica la arquitectura y cita archivos"
.\hermes-ai.ps1 run
```

El scope `quick` ejecuta descubrimiento, ingeniería inversa, arquitectura y calidad. `analysis` añade prácticas, seguridad/NFR y preparación operacional. El scope completo se encuentra catalogado, pero no se ejecutará hasta implementar y validar sus gates de escritura.
