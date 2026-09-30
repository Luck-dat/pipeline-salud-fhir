import os
import psycopg2
import psycopg2.extras
from extract import obtener_pacientes

def cargar_env():
    with open(".env") as archivo:
        for linea in archivo:
            clave, valor = linea.strip().split("=", 1)
            os.environ[clave] = valor

def guardar_pacientes():
    cargar_env()
    datos = obtener_pacientes()
    conexion = psycopg2.connect(
        host="aws-0-us-east-1.pooler.supabase.com",
        port=5432,
        dbname="postgres",
        user="postgres.swlrwlevquhyworrlggv",
        password=os.environ["DB_PASSWORD"]
    )
    cursor = conexion.cursor()

    for entrada in datos.get("entry", []):
        recurso = entrada["resource"]
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

    conexion.commit()
    cursor.close()
    conexion.close()
    print("Pacientes guardados con éxito en Supabase.")

if __name__ == "__main__":
    guardar_pacientes()