import logging
import sqlite3
from contextlib import closing

from errores import ErrorBaseDatos

DB = "academico.db"
logger = logging.getLogger("academico")

_COLUMNAS = "id, nombre, programa, semestre, promedio"


def _conectar():
    conexion = sqlite3.connect(DB)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar():
    try:
        with closing(_conectar()) as conexion:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS estudiantes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    programa TEXT NOT NULL,
                    semestre INTEGER NOT NULL,
                    promedio REAL NOT NULL
                )
            """)
            conexion.commit()
    except sqlite3.Error as e:
        raise ErrorBaseDatos("No se pudo inicializar la base de datos") from e


def listar():
    try:
        with closing(_conectar()) as conexion:
            filas = conexion.execute(f"SELECT {_COLUMNAS} FROM estudiantes").fetchall()
            return [dict(f) for f in filas]
    except sqlite3.Error as e:
        raise ErrorBaseDatos("No se pudo listar los estudiantes") from e


def buscar(id_estudiante):
    try:
        with closing(_conectar()) as conexion:
            fila = conexion.execute(
                f"SELECT {_COLUMNAS} FROM estudiantes WHERE id = ?", (id_estudiante,)
            ).fetchone()
            return dict(fila) if fila else None
    except sqlite3.Error as e:
        raise ErrorBaseDatos(f"No se pudo consultar el estudiante {id_estudiante}") from e


def guardar(estudiante):
    try:
        with closing(_conectar()) as conexion:
            cursor = conexion.execute(
                "INSERT INTO estudiantes(nombre, programa, semestre, promedio) "
                "VALUES (?, ?, ?, ?)",
                (estudiante.nombre, estudiante.programa,
                 estudiante.semestre, estudiante.promedio),
            )
            conexion.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        raise ErrorBaseDatos("No se pudo guardar el estudiante") from e
