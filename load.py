import os
import json
import psycopg2
import psycopg2.extras
from extract import obtener_bundles_pacientes


def cargar_env():
    with open(".env") as archivo:
        for linea in archivo:
            clave, valor = linea.strip().split("=", 1)
            os.environ[clave] = valor


def extraer_id_referencia(referencia):
    """
    Convierte una referencia FHIR tipo 'Patient/abc-123' o
    'urn:uuid:abc-123' en solo el id 'abc-123'.
    """
    if not referencia:
        return None
    return referencia.split("/")[-1].split(":")[-1]


def guardar_paciente(cursor, recurso):
    id_paciente = recurso.get("id")
    nombre_obj = recurso.get("name", [{}])[0]
    nombre = " ".join(nombre_obj.get("given", []))
    apellido = nombre_obj.get("family")
    genero = recurso.get("gender")
    fecha_nacimiento = recurso.get("birthDate")

    cursor.execute("""
        INSERT INTO pacientes (id, nombre, apellido, genero, fecha_nacimiento, fuente_json)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (id_paciente, nombre, apellido, genero, fecha_nacimiento, psycopg2.extras.Json(recurso)))


def guardar_encuentro(cursor, recurso):
    id_encuentro = recurso.get("id")
    id_paciente = extraer_id_referencia(recurso.get("subject", {}).get("reference"))
    fecha = recurso.get("period", {}).get("start")

    tipo_lista = recurso.get("type", [{}])
    tipo = tipo_lista[0].get("text") if tipo_lista else None

    motivo_lista = recurso.get("reasonCode", [{}])
    motivo = None
    if motivo_lista:
        codings = motivo_lista[0].get("coding", [{}])
        motivo = codings[0].get("display") if codings else motivo_lista[0].get("text")

    cursor.execute("""
        INSERT INTO encuentros (id, id_paciente, fecha, tipo, motivo, fuente_json)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (id_encuentro, id_paciente, fecha, tipo, motivo, psycopg2.extras.Json(recurso)))


def guardar_condicion(cursor, recurso):
    id_condicion = recurso.get("id")
    id_paciente = extraer_id_referencia(recurso.get("subject", {}).get("reference"))
    codigo = recurso.get("code", {})
    codings = codigo.get("coding", [{}])
    descripcion = codings[0].get("display") if codings else codigo.get("text")
    fecha_inicio = recurso.get("onsetDateTime")
    fecha_fin = recurso.get("abatementDateTime")

    cursor.execute("""
        INSERT INTO condiciones (id, id_paciente, descripcion, fecha_inicio, fecha_fin, fuente_json)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (id_condicion, id_paciente, descripcion, fecha_inicio, fecha_fin, psycopg2.extras.Json(recurso)))


def guardar_observacion(cursor, recurso):
    id_observacion = recurso.get("id")
    id_paciente = extraer_id_referencia(recurso.get("subject", {}).get("reference"))
    id_encuentro = extraer_id_referencia(recurso.get("encounter", {}).get("reference"))

    codigo_obj = recurso.get("code", {})
    codings = codigo_obj.get("coding", [{}])
    primer_coding = codings[0] if codings else {}
    codigo = primer_coding.get("code")
    descripcion = primer_coding.get("display") or codigo_obj.get("text")

    valor = None
    unidad = None
    if "valueQuantity" in recurso:
        valor = str(recurso["valueQuantity"].get("value"))
        unidad = recurso["valueQuantity"].get("unit")
    elif "valueCodeableConcept" in recurso:
        valor = recurso["valueCodeableConcept"].get("text")

    fecha = recurso.get("effectiveDateTime")

    # El JSON original solo se conserva cuando la observación tiene componentes
    # (por ejemplo presión arterial), porque ahí está el valor que no extraemos.
    fuente = psycopg2.extras.Json(recurso) if "component" in recurso else None

    cursor.execute("""
        INSERT INTO observaciones (id, id_paciente, id_encuentro, codigo, descripcion, valor, unidad, fecha, fuente_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (id_observacion, id_paciente, id_encuentro, codigo, descripcion, valor, unidad, fecha, fuente))

def guardar_medicamento(cursor, recurso):
    id_medicamento = recurso.get("id")
    id_paciente = extraer_id_referencia(recurso.get("subject", {}).get("reference"))
    id_encuentro = extraer_id_referencia(recurso.get("encounter", {}).get("reference"))

    medicamento_obj = recurso.get("medicationCodeableConcept", {})
    codings = medicamento_obj.get("coding", [{}])
    nombre_medicamento = codings[0].get("display") if codings else medicamento_obj.get("text")

    fecha_inicio = recurso.get("authoredOn")
    estado = recurso.get("status")

    cursor.execute("""
        INSERT INTO medicamentos (id, id_paciente, id_encuentro, nombre_medicamento, fecha_inicio, estado, fuente_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (id_medicamento, id_paciente, id_encuentro, nombre_medicamento, fecha_inicio, estado, psycopg2.extras.Json(recurso)))


def guardar_pacientes():
    cargar_env()
    bundles = obtener_bundles_pacientes()

    # ✅ VERSIÓN CORREGIDA: Todo se lee de variables de entorno
    conexion = psycopg2.connect(
        host=os.environ.get("DB_HOST", "aws-0-us-east-1.pooler.supabase.com"),
        port=int(os.environ.get("DB_PORT", 5432)),
        dbname=os.environ.get("DB_NAME", "postgres"),
        user=os.environ.get("DB_USER", "postgres.swlrwlevquhyworrlggv"),
        password=os.environ["DB_PASSWORD"]
    )
    cursor = conexion.cursor()

    # Procesamos en dos pasadas por bundle: primero Patient y Encounter
    # (porque Condition/Observation/MedicationRequest los referencian),
    # después el resto.
    for bundle in bundles:
        entradas = bundle.get("entry", [])

        for entrada in entradas:
            recurso = entrada["resource"]
            tipo = recurso.get("resourceType")
            if tipo == "Patient":
                guardar_paciente(cursor, recurso)
            elif tipo == "Encounter":
                guardar_encuentro(cursor, recurso)

        for entrada in entradas:
            recurso = entrada["resource"]
            tipo = recurso.get("resourceType")
            if tipo == "Condition":
                guardar_condicion(cursor, recurso)
            elif tipo == "Observation":
                guardar_observacion(cursor, recurso)
            elif tipo == "MedicationRequest":
                guardar_medicamento(cursor, recurso)

        # --- ACÁ ESTÁ EL ARREGLO ---
        # Hacemos commit por cada bundle. Si uno falla, no se pierden los anteriores.

        try:
            conexion.commit()
        except Exception as e:
            conexion.rollback()
            print(f"Error al guardar un bundle: {e}")
            continue

    # Esto va afuera del bucle (al final de todo)
        cursor.close()
        conexion.close()
        print("Pacientes y su historia clinica guardados con exito en Supabase.")

if __name__ == "__main__":
    guardar_pacientes()
