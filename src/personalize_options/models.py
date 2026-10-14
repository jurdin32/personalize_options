"""Las opciones, los roles y los permisos por opción.

Una **opción** es una pantalla o un apartado del menú (Clientes, Guías de remisión,
Inventario…). Viven en la base, así que se pueden crear y cambiar sin tocar código
ni migrar: ver :mod:`personalize_options.opciones`, que trae las de serie.

Un **rol** es un permiso con nombre («Facturador», «Bodega»…): se crean los que hagan
falta y se le asignan usuarios. De cada rol se marca, por cada opción, si puede
**leerla** o **leerla y escribirla**; lo que no se marca, no se puede.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from . import opciones as registro

__all__ = ["Opcion", "Nivel", "Rol", "Permiso", "validar_opcion"]


def validar_opcion(clave: str) -> None:
    """Comprueba que la clave sea una de las opciones de la aplicación."""
    if not registro.existe(clave):
        raise ValidationError(f"«{clave}» no es una opción de la aplicación.")


class Opcion(models.Model):
    """Una pantalla o un apartado del menú.

    Se crean desde la aplicación o desde el admin, sin tocar código ni migrar: los
    permisos de los roles se marcan sobre estas opciones. La **clave** es lo que se
    guarda en los permisos y con lo que se pregunta en el código, así que conviene
    no cambiarla una vez en marcha (si se cambia, el paquete mueve los permisos).
    """

    clave = models.SlugField(
        "clave",
        max_length=40,
        unique=True,
        help_text="Con lo que se pregunta en el código: clientes, guias-remision…",
    )
    nombre = models.CharField("nombre", max_length=80)
    grupo = models.CharField(
        "apartado",
        max_length=40,
        help_text="Bajo qué apartado sale en el menú: Catálogo, Comprobantes…",
    )
    orden = models.PositiveIntegerField(
        "orden", default=0, help_text="Con qué orden sale dentro de su apartado."
    )
    url = models.CharField(
        "dirección",
        max_length=200,
        blank=True,
        help_text="Para que salga en el menú, la dirección de la pantalla: /reportes/",
    )
    icono = models.CharField(
        "icono",
        max_length=40,
        blank=True,
        help_text="El icono del menú, sin el «mif-» (report, chart-bar…).",
    )
    en_menu = models.BooleanField(
        "en el menú", default=True, help_text="Solo sale si tiene dirección."
    )
    activo = models.BooleanField(
        "activa",
        default=True,
        help_text="Una opción apagada desaparece del menú y del asistente.",
    )
    creado = models.DateTimeField("creada", auto_now_add=True)
    actualizado = models.DateTimeField("actualizada", auto_now=True)

    class Meta:
        verbose_name = "opción"
        verbose_name_plural = "opciones"
        ordering = ["orden", "nombre"]

    def __str__(self) -> str:
        return f"{self.grupo} · {self.nombre}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Si le cambian la clave, los permisos que había se van con ella."""
        anterior = None
        if self.pk:
            anterior = (
                Opcion.objects.filter(pk=self.pk).values_list("clave", flat=True).first()
            )
        super().save(*args, **kwargs)
        if anterior and anterior != self.clave:
            Permiso.objects.filter(opcion=anterior).update(opcion=self.clave)


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
        """Cómo se llama la opción (su clave, si ya no está)."""
        try:
            return str(registro.de(self.opcion))
        except KeyError:
            return self.opcion


@receiver(post_delete, sender=Opcion)
def _quitar_los_permisos_de_la_opcion(sender: Any, instance: Opcion, **kwargs: Any) -> None:
    """Borrar una opción se lleva por delante los permisos que la nombraban."""
    Permiso.objects.filter(opcion=instance.clave).delete()
