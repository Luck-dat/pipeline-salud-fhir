import json
import os

CARPETA_PACIENTES = os.path.join("output", "fhir")
ARCHIVOS_A_IGNORAR = ("hospitalInformation", "practitionerInformation")

def obtener_pacientes():
    """
    Lee los archivos JSON generados por Synthea en output/fhir/
    y devuelve una lista combinada de 'entry', igual al formato
    que devolvía antes la API pública de FHIR.
    """
    entradas_combinadas = []

    for nombre_archivo in os.listdir(CARPETA_PACIENTES):
        if not nombre_archivo.endswith(".json"):
            continue
        if nombre_archivo.startswith(ARCHIVOS_A_IGNORAR):
            continue

        ruta_completa = os.path.join(CARPETA_PACIENTES, nombre_archivo)
        with open(ruta_completa, "r", encoding="utf-8") as archivo:
            bundle = json.load(archivo)
            entradas_combinadas.extend(bundle.get("entry", []))

    return {"entry": entradas_combinadas}