"""Configuración de logging y middleware de observabilidad."""
import logging
import os
import time
import uuid
from logging.handlers import RotatingFileHandler

from fastapi import Request
from fastapi.responses import JSONResponse

RUTA_LOGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


def configurar_logging() -> logging.Logger:
    """Crea el logger 'academico' con salida a consola y a logs/app.log."""
    logger = logging.getLogger("academico")
    if logger.handlers:
        return logger

    os.makedirs(RUTA_LOGS, exist_ok=True)
    logger.setLevel(logging.INFO)
    formato = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    archivo = RotatingFileHandler(
        os.path.join(RUTA_LOGS, "app.log"),
        maxBytes=1_000_000, backupCount=3, encoding="utf-8",
    )
    archivo.setFormatter(formato)
    consola = logging.StreamHandler()
    consola.setFormatter(formato)

    logger.addHandler(archivo)
    logger.addHandler(consola)
    return logger


async def middleware_observabilidad(request: Request, call_next):
    """Registra fecha/hora, método, endpoint, código, tiempo y resultado.

    No se registra el cuerpo de la solicitud para no guardar datos personales.
    """
    logger = logging.getLogger("academico")
    id_solicitud = uuid.uuid4().hex[:8]
    request.state.id_solicitud = id_solicitud
    inicio = time.perf_counter()

    try:
        respuesta = await call_next(request)
    except Exception:
        duracion = time.perf_counter() - inicio
        logger.exception(
            "[%s] %s %s | 500 | Tiempo: %.3f s | Excepción no controlada",
            id_solicitud, request.method, request.url.path, duracion,
        )
        return JSONResponse(
            status_code=500,
            content={"detalle": "Error interno del servidor", "id_solicitud": id_solicitud},
        )

    duracion = time.perf_counter() - inicio
    codigo = respuesta.status_code
    if codigo < 400:
        nivel, resultado = logging.INFO, "Operación exitosa"
    elif codigo < 500:
        nivel, resultado = logging.WARNING, "Error del cliente"
    else:
        nivel, resultado = logging.ERROR, "Error del servidor"

    logger.log(
        nivel, "[%s] %s %s | %d | Tiempo: %.3f s | %s",
        id_solicitud, request.method, request.url.path, codigo, duracion, resultado,
    )
    respuesta.headers["X-Request-ID"] = id_solicitud
    return respuesta
