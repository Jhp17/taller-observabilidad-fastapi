import logging
import os

import requests

from errores import ErrorServicioExterno
from repositories.estudiante_repository import guardar, listar, buscar

logger = logging.getLogger("academico")

# Se pueden cambiar con variables de entorno (útil para probar con un servidor lento).
URL_API_EXTERNA = os.getenv("API_EXTERNA_URL", "https://jsonplaceholder.typicode.com/users")
TIMEOUT_API_EXTERNA = float(os.getenv("API_EXTERNA_TIMEOUT", "5"))


def consultar_api_externa(programa):
    # Mejoras 3 y 4: timeout explícito y manejo de cada tipo de fallo.
    try:
        respuesta = requests.get(
            URL_API_EXTERNA,
            params={"company": programa},
            timeout=TIMEOUT_API_EXTERNA,
        )
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.Timeout as e:
        raise ErrorServicioExterno(
            f"Tiempo de espera agotado ({TIMEOUT_API_EXTERNA} s)"
        ) from e
    except ValueError as e:  # JSON inválido (va antes de RequestException)
        raise ErrorServicioExterno("La respuesta externa no es un JSON válido") from e
    except requests.RequestException as e:
        raise ErrorServicioExterno(f"Fallo de comunicación: {e.__class__.__name__}") from e


def obtener_estudiantes():
    return listar()


def obtener_estudiante(id_estudiante):
    return buscar(id_estudiante)


def registrar_estudiante(estudiante):
    nuevo_id = guardar(estudiante)
    logger.info("Estudiante registrado con id=%s", nuevo_id)

    # El registro no depende de que el servicio externo esté disponible:
    # si falla, se registra el error y se responde con información parcial.
    try:
        datos = consultar_api_externa(estudiante.programa)
        informacion = {
            "disponible": True,
            "registros_recibidos": len(datos) if isinstance(datos, list) else 1,
        }
    except ErrorServicioExterno as e:
        logger.exception("Fallo del servicio externo al registrar id=%s: %s", nuevo_id, e)
        informacion = {"disponible": False, "motivo": "Servicio externo no disponible"}

    return {"id": nuevo_id, "estudiante": estudiante, "informacion_externa": informacion}
