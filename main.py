from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from errores import ErrorBaseDatos
from observabilidad import configurar_logging, middleware_observabilidad
from repositories.estudiante_repository import inicializar
from routes.estudiantes import router

logger = configurar_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Mejora 1: la tabla se crea al iniciar, antes de recibir solicitudes.
    inicializar()
    logger.info("Base de datos inicializada")
    yield


app = FastAPI(title="Sistema Académico - Taller de Observabilidad", lifespan=lifespan)
app.middleware("http")(middleware_observabilidad)
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def manejar_validacion(request: Request, exc: RequestValidationError):
    # Se registran solo campo y motivo; nunca el valor enviado.
    campos = "; ".join(
        f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()
    )
    logger.warning(
        "[%s] Datos inválidos en %s %s | %s",
        getattr(request.state, "id_solicitud", "-"), request.method, request.url.path, campos,
    )
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(ErrorBaseDatos)
async def manejar_error_bd(request: Request, exc: ErrorBaseDatos):
    id_solicitud = getattr(request.state, "id_solicitud", "-")
    logger.error(
        "[%s] Error de base de datos en %s %s | %s | causa: %r",
        id_solicitud, request.method, request.url.path, exc, exc.__cause__,
    )
    # Al cliente no se le entregan detalles internos.
    return JSONResponse(
        status_code=500,
        content={"detalle": "Error al acceder a la base de datos", "id_solicitud": id_solicitud},
    )


@app.get("/")
def inicio():
    return {"mensaje": "Sistema académico activo"}
