"""Excepciones propias de la aplicación."""


class ErrorBaseDatos(Exception):
    """Fallo al operar sobre la base de datos (la causa original queda en __cause__)."""


class ErrorServicioExterno(Exception):
    """Fallo al comunicarse con el servicio externo (timeout, conexión, HTTP o JSON)."""
