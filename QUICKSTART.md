# Probar Hermes en local

Hermes funciona inicialmente en modo de solo lectura sobre `C:\Trabajos`. No modifica los proyectos escaneados; guarda su inventario dentro de `.hermes/reports/` en este repositorio.

## Comprobar la configuración

```powershell
.\hermes.ps1 doctor
```

## Crear el inventario

```powershell
.\hermes.ps1 scan
```

El reporte legible queda en `.hermes/reports/inventory.md` y los datos estructurados en `.hermes/reports/inventory.json`.

## Revisar un proyecto

```powershell
.\hermes.ps1 show nexora
```

También puede buscar por tecnología:

```powershell
.\hermes.ps1 show "Next.js"
```

## Iniciar la consola de Hermes

```powershell
.\hermes.ps1 run
```

Dentro de la consola están disponibles `proyectos`, `buscar <texto>`, `revisar <proyecto>`, `prioridades`, `ayuda` y `salir`.

## Cambiar las carpetas autorizadas

Edite `hermes.config.json` y agregue rutas absolutas en `workspace_roots`. Este MVP exige `access_mode: read_only`.

## Próxima etapa

Después de validar el inventario local se puede conectar un modelo local mediante Ollama y, más adelante, empaquetar Hermes para un VPS. El acceso de escritura debe diseñarse por proyecto y con aprobación explícita.
