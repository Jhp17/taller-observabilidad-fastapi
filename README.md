# Sistema Académico – Versión 2: con mejoras

Incluye observabilidad y las correcciones de los hallazgos.

| Mejora | Archivo |
| --- | --- |
| Tabla creada al iniciar (`lifespan`) | `main.py` |
| HTTP 404 para recurso inexistente | `routes/estudiantes.py` |
| Timeout configurable en la API externa (5 s) | `services/estudiante_service.py` |
| Manejo de errores externos y de BD, con logging | `services/`, `repositories/`, `errores.py` |
| Validación de rangos (semestre 1–12, promedio 0–5) | `models/estudiante.py` |
| Respuesta sin datos de terceros de la API externa | `services/estudiante_service.py` |
| Conexiones SQLite cerradas siempre; resultados como dict | `repositories/` |

## Ejecución

    python -m pip install -r requirements.txt
    python -m uvicorn main:app --reload
    python -m pytest

Variables opcionales: `API_EXTERNA_URL` y `API_EXTERNA_TIMEOUT` (segundos).

Los logs se guardan en `logs/app.log`. No se incluyen credenciales, tokens ni claves.
