"""Etiquetas y filtros para las plantillas y el menú.

    {% puede_leer "clientes" as ver %}
    {% if ver %} … {% endif %}

    {% if request.permisos.puede_escribir %} … {% endif %}   {# o con el filtro #}
    {% if usuario|puede_escribir:"clientes" %} … {% endif %}
"""

from __future__ import annotations

from typing import Any

from django import template

from .. import opciones as registro
from ..permisos import de, de_la_peticion

register = template.Library()

__all__ = [
    "puede_leer",
    "puede_escribir",
    "opciones_visibles",
    "opciones_del_menu",
    "apartados_nuevos",
    "nombre_de",
]


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


def _activas(context: Any) -> Any:
    """Las opciones activas, leídas una vez por petición (el menú las pide varias)."""
    peticion = context.get("request")
    guardadas = getattr(peticion, "_opciones_activas", None) if peticion else None
    if guardadas is None:
        guardadas = registro.todas(solo_activas=True)
        if peticion is not None:
            peticion._opciones_activas = guardadas
    return guardadas


@register.simple_tag(takes_context=True)
def opciones_del_menu(context: Any, grupo: str, ya_pintadas: str = "") -> Any:
    """Las opciones de un apartado que el menú puede pintar solo.

    Son las que llevan dirección (``url``), están puestas en el menú, el usuario
    puede ver y la plantilla no pinta a mano: así, una opción creada después —desde
    la aplicación o el admin— sale en el menú sin tocar la plantilla.

    ``ya_pintadas`` es la lista de claves que la plantilla ya dibuja en ese apartado,
    separadas por espacios.
    """
    quien = _quien(context)
    de_siempre = set(ya_pintadas.split())
    return [
        opcion
        for opcion in _activas(context)
        if opcion.grupo == grupo
        and opcion.url
        and opcion.en_menu
        and opcion.clave not in de_siempre
        and quien.puede_leer(opcion.clave)
    ]


@register.simple_tag(takes_context=True)
def apartados_nuevos(context: Any, ya_pintados: str = "") -> Any:
    """Los apartados que la plantilla del menú no conoce, con sus opciones.

    Devuelve ``[(apartado, [opciones]), …]`` para los apartados que no estén en
    ``ya_pintados``: si alguien crea un apartado nuevo desde la aplicación, sale en
    el menú como uno más, sin tocar la plantilla.
    """
    conocidos = set(ya_pintados.split())
    quien = _quien(context)
    apartados = []
    for grupo, opciones in registro.grupos(solo_activas=True):
        if grupo in conocidos:
            continue
        visibles = [
            opcion
            for opcion in opciones
            if opcion.en_menu and opcion.url and quien.puede_leer(opcion.clave)
        ]
        if visibles:
            apartados.append((grupo, visibles))
    return apartados


@register.simple_tag
def nombre_de(clave: str) -> str:
    """Cómo se llama una opción (por si hace falta en un aviso)."""
    try:
        return registro.de(clave).nombre
    except KeyError:
        return clave
