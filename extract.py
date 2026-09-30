import requests

def obtener_pacientes():
    url = "https://hapi.fhir.org/baseR4/Patient?_count=5"
    respuesta = requests.get(url)
    respuesta.raise_for_status()
    return respuesta.json()