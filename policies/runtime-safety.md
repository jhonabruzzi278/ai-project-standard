# Seguridad del runtime local

Hermes opera con privilegios mínimos.

- Puede listar carpetas y leer metadatos o archivos de configuración no secretos dentro de las raíces autorizadas.
- Puede escribir inventarios y reportes únicamente en su directorio de estado.
- No puede modificar proyectos reales, ejecutar sus scripts ni instalar dependencias.
- No debe leer el contenido de `.env`, llaves privadas, tokens o almacenes de credenciales.
- No realiza acciones destructivas.

Requieren aprobación explícita del propietario: modificar un proyecto, ejecutar migraciones o despliegues, instalar dependencias, conectarse a servicios externos, operar Git o ampliar las raíces autorizadas.

Un modo de escritura futuro deberá autorizar cada proyecto por separado, mostrar una vista previa de los cambios y ofrecer un mecanismo de reversión.
