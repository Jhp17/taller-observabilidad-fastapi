from pydantic import BaseModel, Field


class Estudiante(BaseModel):
    # Mejora 5: restricciones de rango. Ajuste los límites a las reglas de su curso.
    nombre: str = Field(..., min_length=1, max_length=100)
    programa: str = Field(..., min_length=1, max_length=100)
    semestre: int = Field(..., ge=1, le=12)
    promedio: float = Field(..., ge=0.0, le=5.0)
