 # pipeline-salud-fhir

Pipeline de datos de salud que extrae, transforma y carga historias clínicas sintéticas en una base de datos relacional, siguiendo el estándar FHIR. Corre automáticamente todos los días mediante GitHub Actions y notifica por Telegram si falla.

## Qué hace
*   Genera pacientes sintéticos con historia clínica completa (consultas, diagnósticos, observaciones, medicamentos) usando **Synthea**.
*   Extrae esos datos en formato FHIR (JSON).
*   Los transforma y distribuye en un esquema relacional de 5 tablas en Postgres (Supabase).
*   Corre de forma automática una vez al día, y también se puede disparar manualmente.
*   Incluye tests unitarios con `pytest` y monitoreo con alertas por Telegram.

## Por qué está armado así
Este proyecto pasó por varias decisiones de diseño que vale la pena explicar, porque el camino recorrido importa tanto como el resultado final.

*   **La fuente de datos cambió dos veces.** La primera versión extraía pacientes desde hapi.fhir.org (servidor de pruebas). Funcionaba, pero los datos eran basura de prueba de otra gente. Se reemplazó por **Synthea**, un generador de pacientes 100% sintéticos pero clínicamente coherentes, que corre como parte del propio pipeline.

*   **El esquema de base de datos se rediseñó de una tabla a cinco.** La primera versión guardaba todo en una sola tabla `pacientes`. Al incorporar Synthea, se hizo evidente que cada paciente trae consigo encuentros médicos, diagnósticos, observaciones y medicamentos. Meter todo eso en una tabla plana hubiera sido ignorar la estructura real del dominio. El esquema final tiene `pacientes` en el centro, con `encuentros`, `condiciones`, `observaciones` y `medicamentos` relacionados por foreign keys.

*   **La conexión a la base usa el pooler de transacciones, no la conexión directa.** La conexión directa a Supabase requiere IPv6 por defecto (lo cual implicaría pagar un add-on para IPv4-only). El Transaction pooler resuelve esto sin costo y es la opción recomendada para conexiones cortas.

*   **Las credenciales nunca están hardcodeadas.** Se leen desde variables de entorno (`.env` local, excluido por `.gitignore`) y desde **GitHub Secrets** en la automatización. Nunca expuestas en el código ni en los logs.

*   **Manejo de errores a nivel de lote.** El pipeline procesa los datos y hace `commit` por cada bundle. Si un paciente falla, no se revierte toda la carga, sino que se registra el error y se continúa con el siguiente, garantizando idempotencia.

## Diagrama de arquitectura

```text
Synthea (genera pacientes)
        │
        ▼
output/fhir/*.json
        │
        ▼
  read_bundles.py (lee los bundles FHIR)
        │
        ▼
   load.py (distribuye cada recurso a su tabla con manejo de errores)
        │
        ▼
┌───────────────────────────────────────────┐
│              Supabase (Postgres)           │
│                                             │
│   pacientes ──┬── encuentros                │
│               ├── condiciones               │
│               ├── observaciones             │

```
## Automatización y Monitoreo
El pipeline corre todos los días a las 12:00 UTC mediante GitHub Actions, y también puede dispararse manualmente desde la pestaña Actions. Cada ejecución:
1. Instala Python y Java en una máquina virtual temporal.
2. Instala las dependencias desde `requirements.txt`.
3. Descarga Synthea y genera un nuevo lote de pacientes sintéticos.
4. Carga los datos a Supabase.
5. **Si algo falla, envía una alerta por Telegram con el link a los logs.**

## Tests
El proyecto incluye tests unitarios (con `pytest`) para validar la lógica de extracción de referencias FHIR, asegurando que los formatos `Patient/123` y `urn:uuid:123` se procesen correctamente.

## Stack
*   **Python** — extracción y transformación.
*   **Synthea (Java)** — generación de datos sintéticos en formato FHIR.
*   **PostgreSQL (Supabase)** — almacenamiento relacional.
*   **GitHub Actions** — orquestación y automatización.
*   **Telegram API** — alertas de monitoreo.
*   **Docker** — contenerización (Dockerfile incluido).
*   **Pytest** — testing.
---
## Mejoras pendientes
*   Los inserts a la base se hacen registro por registro; para volúmenes mayores convendría pasar a inserts en lote (`execute_values` de `psycopg2`) para reducir el tiempo de carga.

*Proyecto de portfolio de ingeniería de datos. Abierto a feedback y a oportunidades laborales.*
│               └── medicamentos              │
└───────────────────────────────────────────┘
