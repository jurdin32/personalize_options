"""Los decoradores y las comprobaciones para proteger las vistas.

Los decoradores van **por dentro** de ``@login_required`` (que es el de fuera), para
que a quien no esté identificado se le mande a entrar y no se le enseñe un 403::

    @login_required
    @requiere_escritura("clientes")
    def cliente(request, pk=None): ...

Para la misma pantalla que sirve para ver y para guardar, se pide lectura al entrar
y se pregunta por la escritura en el momento de guardar::

    @login_required
    @requiere_lectura("clientes")
    def cliente(request, pk=None):
        if request.method == "POST":
            exigir_escritura(request, "clientes")   # corta si no puede
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from django.core.exceptions import PermissionDenied

from . import opciones
from .models import Nivel
from .permisos import de_la_peticion

__all__ = [
    "requiere",
    "requiere_lectura",
    "requiere_escritura",
    "exigir",
    "exigir_lectura",
    "exigir_escritura",
]


def _queja(clave: str, nivel: str) -> str:
    try:
        nombre = opciones.de(clave).nombre
    except KeyError:
        nombre = clave
    if nivel == Nivel.ESCRITURA.value:
        return f"No tiene permiso para modificar «{nombre}»."
    return f"No tiene permiso para ver «{nombre}»."


def exigir(request: Any, clave: str, nivel: str = Nivel.LECTURA.value) -> None:
    """Corta la vista con un 403 si el usuario no tiene ese nivel.

    Es lo que hace un decorador, pero para preguntarlo dentro de la vista: una
    pantalla que se ve con lectura y se guarda con escritura lo necesita.
    """
    quien = de_la_peticion(request)
    permitido = (
        quien.puede_escribir(clave)
        if nivel == Nivel.ESCRITURA.value
        else quien.puede_leer(clave)
    )
    if not permitido:
        raise PermissionDenied(_queja(clave, nivel))


def exigir_lectura(request: Any, clave: str) -> None:
    """Corta si no puede **ver** esa opción."""
    exigir(request, clave, Nivel.LECTURA.value)


def exigir_escritura(request: Any, clave: str) -> None:
    """Corta si no puede **modificar** esa opción (incluye verla)."""
    exigir(request, clave, Nivel.ESCRITURA.value)


def requiere(clave: str, nivel: str = Nivel.LECTURA.value) -> Callable:
    """Solo deja pasar a quien tenga ese nivel (o más) en esa opción."""

    def _decorar(vista: Callable) -> Callable:
        @wraps(vista)
        def _envuelta(request: Any, *args: Any, **kwargs: Any) -> Any:
            exigir(request, clave, nivel)
            return vista(request, *args, **kwargs)

        return _envuelta

    return _decorar


def requiere_lectura(clave: str) -> Callable:
    """La vista se puede **ver**."""
    return requiere(clave, Nivel.LECTURA.value)


def requiere_escritura(clave: str) -> Callable:
    """La vista se puede **modificar** (incluye verla)."""
    return requiere(clave, Nivel.ESCRITURA.value)
