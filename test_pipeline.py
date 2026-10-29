import pytest
from load import extraer_id_referencia, transformar_paciente

def test_extraer_id_referencia_paciente():
    assert extraer_id_referencia("Patient/abc-123") == "abc-123"

def test_extraer_id_referencia_urn():
    assert extraer_id_referencia("urn:uuid:xyz-789") == "xyz-789"

def test_extraer_id_referencia_vacio():
    assert extraer_id_referencia(None) is None
    assert extraer_id_referencia("") is None

def test_transformar_paciente():
    recurso = {
        "resourceType": "Patient",
        "id": "123",
        "name": [{"given": ["Lucas"], "family": "Lopez"}],
        "gender": "male",
        "birthDate": "1990-01-01"
    }
    resultado = transformar_paciente(recurso)
    assert resultado[0] == "123"
    assert resultado[1] == "Lucas"
    assert resultado[2] == "Lopez"
    assert resultado[3] == "male"
    assert resultado[4] == "1990-01-01"