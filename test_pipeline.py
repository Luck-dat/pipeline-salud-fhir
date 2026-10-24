import pytest
from load import extraer_id_referencia

def test_extraer_id_referencia_paciente():
    assert extraer_id_referencia("Patient/abc-123") == "abc-123"

def test_extraer_id_referencia_urn():
    assert extraer_id_referencia("urn:uuid:xyz-789") == "xyz-789"

def test_extraer_id_referencia_vacio():
    assert extraer_id_referencia(None) is None
    assert extraer_id_referencia("") is None