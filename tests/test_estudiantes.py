import logging

import pytest
import requests
from fastapi.testclient import TestClient

import repositories.estudiante_repository as repo
import routes.estudiantes as rutas
import services.estudiante_service as servicio
from main import app

ESTUDIANTE_VALIDO = {
    "nombre": "Ana",
    "programa": "Ingeniería de Sistemas",
    "semestre": 5,
    "promedio": 4.2,
}


class RespuestaFalsa:
    """Simula la respuesta de requests sin usar la red."""

    def __init__(self, datos=None, error_http=False, json_invalido=False):
        self.datos = datos if datos is not None else []
        self.error_http = error_http
        self.json_invalido = json_invalido

    def raise_for_status(self):
        if self.error_http:
            raise requests.HTTPError("500 Server Error")

    def json(self):
        if self.json_invalido:
            raise ValueError("JSON inválido")
        return self.datos


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Base de datos temporal: las pruebas no tocan academico.db.
    monkeypatch.setattr(repo, "DB", str(tmp_path / "test.db"))
    with TestClient(app) as c:  # el 'with' ejecuta el lifespan (crea la tabla)
        yield c


@pytest.fixture
def api_externa_ok(monkeypatch):
    monkeypatch.setattr(
        servicio.requests, "get",
        lambda *a, **k: RespuestaFalsa(datos=[{"id": 1}, {"id": 2}]),
    )


# ---------- operaciones exitosas ----------

def test_listar_estudiantes_vacio(client):
    respuesta = client.get("/estudiantes/")
    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_crear_estudiante(client, api_externa_ok):
    respuesta = client.post("/estudiantes/", json=ESTUDIANTE_VALIDO)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["id"] == 1
    assert cuerpo["informacion_externa"] == {"disponible": True, "registros_recibidos": 2}


def test_consultar_estudiante_existente(client, api_externa_ok):
    client.post("/estudiantes/", json=ESTUDIANTE_VALIDO)
    respuesta = client.get("/estudiantes/1")
    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Ana"


def test_respuesta_no_expone_datos_de_terceros(client, monkeypatch):
    datos = [{"id": 1, "email": "otra.persona@example.com"}]
    monkeypatch.setattr(servicio.requests, "get", lambda *a, **k: RespuestaFalsa(datos=datos))
    respuesta = client.post("/estudiantes/", json=ESTUDIANTE_VALIDO)
    assert "otra.persona@example.com" not in respuesta.text


# ---------- recursos inexistentes ----------

def test_estudiante_inexistente(client):
    respuesta = client.get("/estudiantes/99999")
    assert respuesta.status_code == 404


def test_identificador_invalido(client):
    assert client.get("/estudiantes/0").status_code == 422
    assert client.get("/estudiantes/abc").status_code == 422


# ---------- validación de datos ----------

@pytest.mark.parametrize("cambio", [
    {"semestre": -1},
    {"semestre": 0},
    {"semestre": 99},
    {"promedio": 8},
    {"promedio": -0.5},
    {"semestre": "cinco"},
    {"promedio": "alto"},
    {"nombre": ""},
])
def test_datos_invalidos_son_rechazados(client, cambio):
    datos = {**ESTUDIANTE_VALIDO, **cambio}
    assert client.post("/estudiantes/", json=datos).status_code == 422


def test_campo_faltante(client):
    datos = {k: v for k, v in ESTUDIANTE_VALIDO.items() if k != "nombre"}
    assert client.post("/estudiantes/", json=datos).status_code == 422


# ---------- servicio externo ----------

def test_llamada_externa_usa_timeout(client, monkeypatch):
    capturado = {}

    def falso(*args, **kwargs):
        capturado.update(kwargs)
        return RespuestaFalsa()

    monkeypatch.setattr(servicio.requests, "get", falso)
    client.post("/estudiantes/", json=ESTUDIANTE_VALIDO)
    assert capturado.get("timeout")


def _lanza(excepcion):
    def falso(*args, **kwargs):
        raise excepcion
    return falso


@pytest.mark.parametrize("comportamiento", [
    _lanza(requests.Timeout("sin respuesta")),
    _lanza(requests.ConnectionError("sin conexión")),
    lambda *a, **k: RespuestaFalsa(error_http=True),
    lambda *a, **k: RespuestaFalsa(json_invalido=True),
], ids=["timeout", "conexion", "http_500", "json_invalido"])
def test_fallo_externo_no_rompe_el_registro(client, monkeypatch, comportamiento):
    monkeypatch.setattr(servicio.requests, "get", comportamiento)
    respuesta = client.post("/estudiantes/", json=ESTUDIANTE_VALIDO)
    assert respuesta.status_code == 201
    assert respuesta.json()["informacion_externa"]["disponible"] is False
    assert len(client.get("/estudiantes/").json()) == 1


# ---------- errores de base de datos y excepciones inesperadas ----------

def test_error_de_bd_devuelve_500_sin_detalles_internos(client, monkeypatch, tmp_path):
    monkeypatch.setattr(repo, "DB", str(tmp_path / "no_existe" / "x.db"))
    respuesta = client.get("/estudiantes/")
    assert respuesta.status_code == 500
    assert "id_solicitud" in respuesta.json()
    assert "sqlite" not in respuesta.text.lower()


def test_excepcion_inesperada_devuelve_500_controlado(client, monkeypatch):
    def falla():
        raise RuntimeError("fallo inesperado")

    monkeypatch.setattr(rutas, "obtener_estudiantes", falla)
    respuesta = client.get("/estudiantes/")
    assert respuesta.status_code == 500
    assert respuesta.json()["detalle"] == "Error interno del servidor"


# ---------- observabilidad ----------

def test_se_registra_la_solicitud(client, caplog):
    with caplog.at_level(logging.INFO, logger="academico"):
        client.get("/estudiantes/")
    assert any(
        "GET /estudiantes/" in m and "| 200 |" in m and "Tiempo:" in m
        for m in caplog.messages
    )


def test_se_registra_el_error_de_validacion(client, caplog):
    with caplog.at_level(logging.WARNING, logger="academico"):
        client.post("/estudiantes/", json={**ESTUDIANTE_VALIDO, "semestre": -1})
    assert any("Datos inválidos" in m and "semestre" in m for m in caplog.messages)
