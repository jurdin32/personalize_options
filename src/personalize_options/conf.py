"""Los ajustes del paquete, con sus valores por omisión.

Se leen de ``settings.PERSONALIZE_OPTIONS`` y se pueden cambiar sin tocar el código::

    PERSONALIZE_OPTIONS = {
        # "abierto": quien no tenga ningún rol puede todo (por omisión, para poder
        #   montar los roles sin dejar a nadie fuera). "cerrado": solo lo que los
        #   roles permitan.
        "MODO": "abierto",
        # Los superusuarios de Django pueden todo, aunque no tengan rol.
        "SUPERUSUARIOS_TODO": True,
    }
"""

from __future__ import annotations

from typing import Any

from django.conf import settings

__all__ = ["AJUSTES", "MODO_ABIERTO", "MODO_CERRADO", "obtener", "modo", "es_abierto", "superusuarios_todo"]

#: Nombre del ajuste en ``settings``.
AJUSTES = "PERSONALIZE_OPTIONS"

MODO_ABIERTO = "abierto"
MODO_CERRADO = "cerrado"

#: Los valores de serie.
POR_OMISION: dict[str, Any] = {
    "MODO": MODO_ABIERTO,
    "SUPERUSUARIOS_TODO": True,
}


def obtener(nombre: str, por_defecto: Any = None) -> Any:
    """Un ajuste de ``SEGURIDAD``, con el valor de serie si no está."""
    configurados = getattr(settings, AJUSTES, None) or {}
    if nombre in configurados:
        return configurados[nombre]
    if por_defecto is not None:
        return por_defecto
    return POR_OMISION.get(nombre)


def modo() -> str:
    """«abierto» o «cerrado» (lo que no se reconozca se toma como abierto)."""
    valor = str(obtener("MODO", MODO_ABIERTO)).strip().lower()
    return MODO_CERRADO if valor == MODO_CERRADO else MODO_ABIERTO


def es_abierto() -> bool:
    """¿Quien no tiene ningún rol puede pasar?"""
    return modo() == MODO_ABIERTO


def superusuarios_todo() -> bool:
    """¿Los superusuarios de Django pueden todo, aunque no tengan rol?"""
    return bool(obtener("SUPERUSUARIOS_TODO", True))
