"""Lo que puede hacer un usuario: sus niveles por opción, ya resueltos.

Si un usuario tiene varios roles, vale **el más alto** de ellos: el que puede
escribir manda sobre el que solo puede leer. Un superusuario de Django puede todo
(se puede apagar con ``PERSONALIZE_OPTIONS["SUPERUSUARIOS_TODO"] = False``).

Con el modo abierto (el de serie), quien **no tenga ningún rol** puede todo: así se
puede montar la seguridad sin dejar a nadie fuera de la aplicación. Cuando los roles
están puestos, se cambia a ``"cerrado"`` y solo se puede lo que los roles permitan.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Set

from . import conf, opciones
from .models import Nivel, Permiso, Rol

__all__ = ["Permisos", "de", "de_la_peticion", "PESO"]

logger = logging.getLogger(__name__)

#: Peso de cada nivel, para quedarse con el más alto cuando hay varios roles.
PESO: Dict[str, int] = {
    "": 0,
    Nivel.LECTURA.value: 1,
    Nivel.ESCRITURA.value: 2,
}


class Permisos:
    """Los permisos de un usuario."""

    def __init__(self, usuario: Any) -> None:
        self.usuario = usuario
        self.autenticado = bool(getattr(usuario, "is_authenticated", False))
        self.superusuario = bool(getattr(usuario, "is_superuser", False))
        self._tiene_roles: Optional[bool] = None
        # Las opciones se leen una vez: las de la base (o las de serie, si el
        # paquete todavía no está migrado).
        self._opciones = opciones.todas(solo_activas=True)
        self._claves = {opcion.clave for opcion in self._opciones}
        self._niveles = self._resolver()

    # ------------------------------------------------------------ qué puede

    def nivel(self, clave: str) -> str:
        """Lo que puede en esa opción: ``"escritura"``, ``"lectura"`` o nada."""
        return self._niveles.get(clave, "")

    def puede_leer(self, clave: str) -> bool:
        return self._alcanza(clave, Nivel.LECTURA.value)

    def puede_escribir(self, clave: str) -> bool:
        return self._alcanza(clave, Nivel.ESCRITURA.value)

    @property
    def visibles(self) -> Set[str]:
        """Las claves de las opciones que puede leer (lo que enseña el menú)."""
        return {
            opcion.clave for opcion in self._opciones if self.puede_leer(opcion.clave)
        }

    @property
    def tiene_roles(self) -> bool:
        """¿Tiene algún rol activo? (se pregunta solo si hace falta)."""
        if self._tiene_roles is None:
            self._tiene_roles = bool(
                self.autenticado
                and Rol.objects.filter(activo=True, usuarios=self.usuario).exists()
            )
        return self._tiene_roles

    @property
    def es_abierto(self) -> bool:
        """¿Puede todo por no tener ningún rol (modo abierto)?"""
        return conf.es_abierto() and not self.tiene_roles

    # ------------------------------------------------------------ por dentro

    def _alcanza(self, clave: str, nivel: str) -> bool:
        if not self.autenticado:
            return False
        if clave not in self._claves:
            # Una clave que no es opción (una errata en el decorador) **no** se
            # deja pasar: antes se dejaba, así que una opción desactivada o mal
            # escrita abría la pantalla a todo el mundo.
            logger.warning(
                "Se preguntó por la opción «%s», que no está declarada: se niega.", clave
            )
            return False
        if PESO.get(self.nivel(clave), 0) >= PESO[nivel]:
            return True
        return self.es_abierto

    def _resolver(self) -> Dict[str, str]:
        """El nivel más alto que le dan sus roles, opción por opción."""
        if not self.autenticado:
            return {}
        if self.superusuario and conf.superusuarios_todo():
            return {opcion.clave: Nivel.ESCRITURA.value for opcion in self._opciones}

        filas = Permiso.objects.filter(
            rol__activo=True, rol__usuarios=self.usuario
        ).values_list("opcion", "nivel")
        niveles: Dict[str, str] = {}
        for opcion, nivel in filas:
            if PESO.get(nivel, 0) > PESO.get(niveles.get(opcion, ""), 0):
                niveles[opcion] = nivel
        return niveles


def de(usuario: Any) -> Permisos:
    """Los permisos de un usuario (para el código que no tiene una petición)."""
    return Permisos(usuario)


def de_la_peticion(request: Any) -> Permisos:
    """Los permisos de la petición: los que dejó el middleware, o se calculan.

    Se calculan si el middleware no está puesto, para que las plantillas y los
    decoradores funcionen igual.
    """
    colgados = getattr(request, "permisos", None)
    if isinstance(colgados, Permisos):
        return colgados
    return Permisos(getattr(request, "user", None))
