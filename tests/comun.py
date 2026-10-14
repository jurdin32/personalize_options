"""Lo que comparten las pruebas: los dos modos y un rol listo para usar."""

from __future__ import annotations

from django.contrib.auth.models import User

from personalize_options.models import Permiso, Rol

__all__ = ["SIN_ROLES", "CERRADO", "rol_con"]

#: El modo de serie: quien no tenga rol puede todo.
SIN_ROLES = {"MODO": "abierto", "SUPERUSUARIOS_TODO": True}

#: El modo de una aplicación ya en marcha: solo lo que los roles permitan.
CERRADO = {"MODO": "cerrado", "SUPERUSUARIOS_TODO": True}


def rol_con(nombre: str, usuario: User, **niveles: str) -> Rol:
    """Un rol activo para ese usuario, con las opciones que se indiquen."""
    rol = Rol.objects.create(nombre=nombre)
    rol.usuarios.add(usuario)
    for opcion, nivel in niveles.items():
        Permiso.objects.create(rol=rol, opcion=opcion, nivel=nivel)
    return rol
