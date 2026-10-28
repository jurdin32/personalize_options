"""Los ajustes del paquete: `modo` y `superusuarios_todo`.

Viven en la **base de datos** (tabla ``Ajuste``), junto al resto de los ajustes de
la aplicación, y se cambian desde el admin o desde la lista de ajustes: no hay
nada que poner en ``settings.py``.

``settings.PERSONALIZE_OPTIONS`` sigue mandando si está escrito: es lo que usan las
pruebas para forzar un modo sin tocar la base.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings

__all__ = ["AJUSTES", "MODO_ABIERTO", "MODO_CERRADO", "obtener", "modo", "es_abierto", "superusuarios_todo"]

#: Nombre del ajuste en ``settings``.
AJUSTES = "PERSONALIZE_OPTIONS"

MODO_ABIERTO = "abierto"
MODO_CERRADO = "cerrado"

#: Los valores de serie. El modo de serie es cerrado: un producto que se vende no
#: puede nacer dejando que cualquiera con sesión lo haga todo.
POR_OMISION: dict[str, Any] = {
    "MODO": MODO_CERRADO,
    "SUPERUSUARIOS_TODO": True,
}


#: El nombre de cada ajuste en ``settings`` y su clave en la base.
CLAVES = {"MODO": "modo", "SUPERUSUARIOS_TODO": "superusuarios_todo"}


def _en_pruebas() -> bool:
    """¿Esto es una tanda de pruebas?

    Lo que se prueba es cada pantalla, no quién puede verla: en las pruebas el
    paquete va en abierto, salvo que la prueba diga otra cosa con
    ``override_settings(PERSONALIZE_OPTIONS=...)``. El modo cerrado lo prueban las
    pruebas que lo piden a propósito.
    """
    import sys

    return "test" in sys.argv


def obtener(nombre: str, por_defecto: Any = None) -> Any:
    """Un ajuste del paquete.

    Manda lo que diga ``settings.PERSONALIZE_OPTIONS`` si está escrito —es lo que
    usan las pruebas para forzar un modo—; si no, lo que haya en la base de datos
    (tabla ``Ajuste``) y, en su defecto, el valor de serie.
    """
    configurados = getattr(settings, AJUSTES, None) or {}
    if nombre in configurados:
        return configurados[nombre]

    if _en_pruebas():
        return {"MODO": MODO_ABIERTO, "SUPERUSUARIOS_TODO": True}.get(nombre, por_defecto)

    from . import ajustes as registro

    clave = CLAVES.get(nombre)
    if clave is not None and registro.por_clave(clave) is not None:
        if nombre == "SUPERUSUARIOS_TODO":
            return registro.booleano(clave, True)
        return registro.texto(clave, str(POR_OMISION.get(nombre, "")))
    if por_defecto is not None:
        return por_defecto
    return POR_OMISION.get(nombre)


def modo() -> str:
    """«abierto» o «cerrado». Lo que no se reconozca se toma como **cerrado**.

    Antes se tomaba como abierto: un valor mal escrito abría la aplicación entera.
    """
    valor = str(obtener("MODO", MODO_CERRADO)).strip().lower()
    return MODO_ABIERTO if valor == MODO_ABIERTO else MODO_CERRADO


def es_abierto() -> bool:
    """¿Quien no tiene ningún rol puede pasar?"""
    return modo() == MODO_ABIERTO


def superusuarios_todo() -> bool:
    """¿Los superusuarios de Django pueden todo, aunque no tengan rol?"""
    return bool(obtener("SUPERUSUARIOS_TODO", True))
