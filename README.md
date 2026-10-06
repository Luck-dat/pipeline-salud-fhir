# pipeline-salud-fhir

Pipeline de datos de salud que extrae, transforma y carga historias clínicas sintéticas en una base de datos relacional, siguiendo el estándar FHIR. Corre automáticamente todos los días mediante GitHub Actions.

## Qué hace

1. Genera pacientes sintéticos con historia clínica completa (consultas, diagnósticos, observaciones, medicamentos) usando [Synthea](https://github.com/synthetichealth/synthea).
2. Extrae esos datos en formato FHIR (JSON).
3. Los transforma y distribuye en un esquema relacional de 5 tablas en Postgres (Supabase).
4. Corre de forma automática una vez al día, y también se puede disparar manualmente.

## Por qué está armado así

Este proyecto pasó por varias decisiones de diseño que vale la pena explicar, porque el camino recorrido importa tanto como el resultado final.

**La fuente de datos cambió dos veces.** La primera versión extraía pacientes desde `hapi.fhir.org`, un servidor público de pruebas que cualquier desarrollador en el mundo usa para testear. Funcionaba, pero los datos que traía eran basura de prueba de otra gente: pacientes con nombres como "TestDaniel" o "SyntheticAudit", sin coherencia clínica real. Para un proyecto que busca simular un caso de uso serio, esa fuente no alcanzaba. Se reemplazó por Synthea, un generador de pacientes 100% sintéticos pero clínicamente coherentes, que corre como parte del propio pipeline.

**El esquema de base de datos se rediseñó de una tabla a cinco.** La primera versión guardaba todo en una sola tabla `pacientes`, con los datos del paciente nada más. Al incorporar Synthea se hizo evidente que cada paciente trae consigo mucho más que su nombre y fecha de nacimiento: encuentros médicos, diagnósticos, observaciones clínicas y medicamentos recetados. Meter todo eso en una tabla plana hubiera sido ignorar la estructura real del dominio. El esquema final tiene `pacientes` en el centro, con `encuentros`, `condiciones`, `observaciones` y `medicamentos` relacionados por foreign keys — así cada entidad vive donde corresponde y la integridad referencial queda garantizada por la propia base.

**La conexión a la base usa el pooler de transacciones, no la conexión directa.** La conexión directa a Supabase requiere IPv6 por defecto, lo cual hubiera implicado pagar un add-on para redes IPv4-only (como la mayoría de las conexiones hogareñas). El Transaction pooler resuelve esto sin costo adicional y es la opción recomendada para conexiones cortas como las de este pipeline.

**Las credenciales nunca están en el código.** La contraseña de la base vive en una variable de entorno, cargada desde un archivo `.env` que está explícitamente excluido del repositorio (`.gitignore`). En la automatización de GitHub Actions, la contraseña se guarda como [Secret](https://docs.github.com/en/actions/security-guides/encrypted-secrets) del repositorio, nunca expuesta en el código ni en los logs.

## Arquitectura
Synthea (genera pacientes)
│
▼
output/fhir/*.json
│
▼
extract.py (lee los bundles FHIR)
│
▼
load.py (distribuye cada recurso a su tabla)
│
▼
┌───────────────────────────────────────────┐
│ Supabase (Postgres) │
│ │
│ pacientes ──┬── encuentros │
│ ├── condiciones │
│ ├── observaciones │
│ └── medicamentos │
└───────────────────────────────────────────┘

## Automatización

El pipeline corre todos los días a las 12:00 UTC mediante GitHub Actions, y también puede dispararse manualmente desde la pestaña **Actions** del repositorio. Cada ejecución:

1. Instala Python y Java en una máquina virtual temporal.
2. Descarga Synthea y genera un nuevo lote de pacientes sintéticos.
3. Carga los datos a Supabase.

Como cada corrida genera pacientes distintos, la base crece con cada ejecución — simulando una fuente de datos real que entrega información nueva en cada ciclo, no un dataset estático.

## Stack

- **Python** — extracción y transformación
- **Synthea** (Java) — generación de datos sintéticos en formato FHIR
- **PostgreSQL (Supabase)** — almacenamiento relacional
- **GitHub Actions** — orquestación y automatización
- **Docker** — contenerización (`Dockerfile` incluido)

## Mejoras pendientes

- Los inserts a la base se hacen registro por registro; para volúmenes mayores convendría pasar a inserts en lote (`execute_values` de psycopg2) para reducir el tiempo de carga.
- No hay tests automatizados todavía.

---

Este es mi tercer proyecto de portfolio en el camino de reconversión hacia ingeniería de datos. Estoy abierto a feedback y a oportunidades como data engineer junior.
