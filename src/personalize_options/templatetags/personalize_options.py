"""Etiquetas y filtros para las plantillas y el menú.

    {% puede_leer "clientes" as ver %}
    {% if ver %} … {% endif %}

    {% if request.permisos.puede_escribir %} … {% endif %}   {# o con el filtro #}
    {% if usuario|puede_escribir:"clientes" %} … {% endif %}
"""

from __future__ import annotations

from typing import Any

from django import template

from ..opciones import POR_CLAVE
from ..permisos import de, de_la_peticion

register = template.Library()

__all__ = ["puede_leer", "puede_escribir", "opciones_visibles", "nombre_de"]


def _quien(context: Any) -> Any:
    peticion = context.get("request")
    if peticion is not None:
        return de_la_peticion(peticion)
    return de(context.get("user"))


@register.simple_tag(takes_context=True)
def puede_leer(context: Any, clave: str) -> bool:
    """¿El usuario de la plantilla puede ver esa opción?"""
    return _quien(context).puede_leer(clave)


@register.simple_tag(takes_context=True)
def puede_escribir(context: Any, clave: str) -> bool:
    """¿El usuario de la plantilla puede modificar esa opción?"""
    return _quien(context).puede_escribir(clave)


@register.simple_tag(takes_context=True)
def opciones_visibles(context: Any) -> Any:
    """Las claves de las opciones que puede ver (lo que se enseña en el menú)."""
    return _quien(context).visibles


@register.filter(name="puede_leer")
def puede_leer_de(usuario: Any, clave: str) -> bool:
    """``{{ usuario|puede_leer:"clientes" }}``"""
    return de(usuario).puede_leer(clave)


@register.filter(name="puede_escribir")
def puede_escribir_de(usuario: Any, clave: str) -> bool:
    """``{{ usuario|puede_escribir:"clientes" }}``"""
    return de(usuario).puede_escribir(clave)


@register.simple_tag
def nombre_de(clave: str) -> str:
    """Cómo se llama una opción (por si hace falta en un aviso)."""
    return POR_CLAVE[clave].nombre if clave in POR_CLAVE else clave
