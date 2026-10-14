"""Los roles y sus permisos por opción.

Un **rol** es un permiso con nombre («Facturador», «Bodega»…): se crean los que
hagan falta, sin tocar código, y se le asignan usuarios. De cada rol se marca, por
cada opción de la aplicación, si puede **leerla** o **leerla y escribirla**; lo que
no se marca, no se puede.
"""

from __future__ import annotations

from typing import Dict, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .opciones import OPCIONES, existe

__all__ = ["Nivel", "Rol", "Permiso", "validar_opcion"]


def validar_opcion(clave: str) -> None:
    """Comprueba que la clave sea una de las opciones declaradas.

    Las opciones no se guardan en la tabla (se declaran en
    :mod:`personalize_options.opciones`), así que esto es lo que avisa de una
    clave mal escrita.
    """
    if not existe(clave):
        raise ValidationError(f"«{clave}» no es una opción de la aplicación.")


class Nivel(models.TextChoices):
    """Cuánto se puede hacer en una opción."""

    LECTURA = "lectura", "Solo lectura"
    ESCRITURA = "escritura", "Lectura y escritura"


class Rol(models.Model):
    """Un permiso con nombre, que se le da a los usuarios que lo necesiten."""

    nombre = models.CharField("nombre", max_length=80, unique=True)
    descripcion = models.CharField("descripción", max_length=200, blank=True)
    activo = models.BooleanField(
        "activo", default=True, help_text="Solo los roles activos dan permisos."
    )
    usuarios = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name="usuarios", blank=True, related_name="roles",
        help_text="A quién se le da este rol.",
    )
    creado = models.DateTimeField("creado", auto_now_add=True)
    actualizado = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        verbose_name = "rol"
        verbose_name_plural = "roles"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre

    def nivel(self, clave: str) -> str:
        """Lo que este rol permite en esa opción (``""`` si nada)."""
        permiso = self.permisos.filter(opcion=clave).first()
        return permiso.nivel if permiso else ""

    @property
    def opciones(self) -> Dict[str, str]:
        """Las opciones que permite, con su nivel."""
        return {permiso.opcion: permiso.nivel for permiso in self.permisos.all()}


class Permiso(models.Model):
    """Lo que un rol puede hacer en una opción: nada, leer, o leer y escribir.

    Lo que no tenga fila, no se puede: así, quitar un permiso es quitar la fila y
    no hay que acordarse de volver a marcar «ninguno».
    """

    rol = models.ForeignKey(
        Rol, verbose_name="rol", on_delete=models.CASCADE, related_name="permisos"
    )
    # Sin ``choices``: las opciones se declaran en opciones.py y se pueden añadir o
    # quitar cuando haga falta, sin migración de por medio (lo comprueba
    # tests/test_migraciones.py).
    opcion = models.CharField(
        "opción", max_length=40, validators=[validar_opcion],
        help_text="Las opciones las declara el paquete: ver opciones.py.",
    )
    nivel = models.CharField(
        "permiso", max_length=10, choices=Nivel.choices, default=Nivel.LECTURA
    )

    class Meta:
        verbose_name = "permiso"
        verbose_name_plural = "permisos"
        ordering = ["rol__nombre", "opcion"]
        constraints = [
            models.UniqueConstraint(
                fields=["rol", "opcion"], name="personalize_options_un_permiso_por_opcion"
            )
        ]

    def __str__(self) -> str:
        return f"{self.rol} · {self.descripcion_opcion} · {self.get_nivel_display()}"

    @property
    def descripcion_opcion(self) -> Optional[str]:
        """Cómo se llama la opción (por si ya no está declarada)."""
        return next((str(o) for o in OPCIONES if o.clave == self.opcion), self.opcion)
