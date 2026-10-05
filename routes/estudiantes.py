import logging

from fastapi import APIRouter, HTTPException, Path

from models.estudiante import Estudiante
from services.estudiante_service import (
    obtener_estudiantes, obtener_estudiante, registrar_estudiante
)

logger = logging.getLogger("academico")
router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])


@router.get("/")
def listar_estudiantes():
    return obtener_estudiantes()


@router.get("/{id_estudiante}")
def consultar_estudiante(id_estudiante: int = Path(..., ge=1)):
    estudiante = obtener_estudiante(id_estudiante)

    # Mejora 2: recurso inexistente -> HTTP 404.
    if not estudiante:
        logger.warning("Estudiante id=%s no encontrado", id_estudiante)
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    return estudiante


@router.post("/", status_code=201)
def crear_estudiante(estudiante: Estudiante):
    return registrar_estudiante(estudiante)
