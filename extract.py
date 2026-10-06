import json
import os

CARPETA_PACIENTES = os.path.join("output", "fhir")
ARCHIVOS_A_IGNORAR = ("hospitalInformation", "practitionerInformation")

def obtener_bundles_pacientes():
    """
    Lee cada archivo JSON generado por Synthea en output/fhir/
    y devuelve una lista de bundles completos (uno por paciente),
    sin aplanar ni filtrar los recursos internos.
    """
    bundles = []

    for nombre_archivo in os.listdir(CARPETA_PACIENTES):
        if not nombre_archivo.endswith(".json"):
            continue
        if nombre_archivo.startswith(ARCHIVOS_A_IGNORAR):
            continue

        ruta_completa = os.path.join(CARPETA_PACIENTES, nombre_archivo)
        with open(ruta_completa, "r", encoding="utf-8") as archivo:
            bundle = json.load(archivo)
            bundles.append(bundle)

    return bundles