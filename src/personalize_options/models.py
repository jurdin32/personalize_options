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

__all__ = ["Ajuste", "Categoria", "Opcion", "Nivel", "Rol", "Permiso", "validar_opcion"]


def validar_opcion(clave: str) -> None:
    """Comprueba que la clave sea una de las opciones de la aplicación."""
    if not registro.existe(clave):
        raise ValidationError(f"«{clave}» no es una opción de la aplicación.")


class Categoria(models.Model):
    """Una categoría de permisos: agrupa las opciones para repartirlas por roles.

    Es lo que en el asistente del rol separa «Ventas» de «Contabilidad», y lo que en
    el menú hace de apartado. Se crean y se renombran desde la aplicación, sin tocar
    código: una categoría nueva aparece en los dos sitios en cuanto se le pone una
    opción dentro.
    """

    nombre = models.CharField("nombre", max_length=60, unique=True)
    descripcion = models.CharField(
        "descripción",
        max_length=200,
        blank=True,
        help_text="Para qué es esta categoría: lo que se lee bajo el título.",
    )
    orden = models.PositiveSmallIntegerField(
        "orden", default=100, help_text="Con qué orden sale entre las demás categorías."
    )
    icono = models.CharField(
        "icono", max_length=40, blank=True, help_text="El del menú, sin el «mif-»."
    )
    activa = models.BooleanField(
        "activa",
        default=True,
        help_text="Una categoría apagada no da permisos a las opciones que tenga.",
    )
    creado = models.DateTimeField("creada", auto_now_add=True)
    actualizado = models.DateTimeField("actualizada", auto_now=True)

    class Meta:
        verbose_name = "categoría de permisos"
        verbose_name_plural = "categorías de permisos"
        ordering = ["orden", "nombre"]

    def __str__(self) -> str:
        return self.nombre

    @property
    def cuantas(self) -> int:
        """Cuántas opciones tiene dentro."""
        return self.opciones.count()


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
    categoria = models.ForeignKey(
        Categoria,
        verbose_name="categoría",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opciones",
        help_text="Con qué otras opciones se agrupa en el asistente del rol.",
    )
    grupo = models.CharField(
        "apartado",
        max_length=40,
        blank=True,
        help_text="Se copia de la categoría: es lo que lee el menú.",
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
        return f"{self.categoria_nombre} · {self.nombre}"

    @property
    def categoria_nombre(self) -> str:
        """La categoría a la que pertenece (o el apartado suelto, si no tiene)."""
        return self.categoria.nombre if self.categoria_id else self.grupo

    @property
    def categoria_orden(self) -> int:
        """Con qué orden sale su categoría."""
        return self.categoria.orden if self.categoria_id else 1000

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Si le cambian la clave, los permisos que había se van con ella.

        Además, el apartado se copia de la categoría: el menú sigue leyendo
        ``grupo`` y no hay que tocar las plantillas.
        """
        if self.categoria_id:
            self.grupo = self.categoria.nombre
        elif self.grupo:
            # Una opción que llega con el apartado escrito —lo que hacen las
            # migraciones de los proyectos— busca su categoría por el nombre: así
            # también cae donde tiene que caer.
            self.categoria = Categoria.objects.filter(nombre=self.grupo).first()
        anterior = None
        if self.pk:
            anterior = (
                Opcion.objects.filter(pk=self.pk).values_list("clave", flat=True).first()
            )
        super().save(*args, **kwargs)
        if anterior and anterior != self.clave:
            Permiso.objects.filter(opcion=anterior).update(opcion=self.clave)


class Ajuste(models.Model):
    """Un ajuste de la aplicación: lo que antes iba en ``settings.py``.

    Cada paquete declara los suyos con su valor de serie (ver
    :mod:`personalize_options.ajustes`) y la tabla los guarda. De la declaración
    viene todo menos el **valor**: la clave, el tipo, el grupo, para qué sirve y
    quién lo declara no se escriben a mano, así que no se editan; lo que se
    cambia —desde el admin o desde la aplicación— es el valor.
    """

    class Tipo(models.TextChoices):
        TEXTO = "texto", "Texto"
        ENTERO = "entero", "Número entero"
        BOOLEANO = "booleano", "Sí o no"
        LISTA = "lista", "Lista separada por comas"

    clave = models.SlugField(
        "clave",
        max_length=60,
        unique=True,
        help_text="Con lo que se lee en el código: bloqueo_inactividad_minutos…",
    )
    valor = models.TextField("valor", blank=True)
    tipo = models.CharField("tipo", max_length=10, choices=Tipo.choices, default=Tipo.TEXTO)
    origen = models.CharField(
        "origen",
        max_length=40,
        blank=True,
        help_text="El paquete o la aplicación que lo declara: sale de su declaración.",
    )
    grupo = models.CharField(
        "grupo", max_length=40, blank=True, help_text="Para agruparlos en el admin."
    )
    descripcion = models.CharField(
        "descripción", max_length=220, blank=True, help_text="Para qué es este ajuste."
    )
    orden = models.PositiveIntegerField("orden", default=0)
    editable = models.BooleanField(
        "editable",
        default=True,
        help_text="Los que no lo son sólo los pone el paquete que los declara.",
    )
    actualizado = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        verbose_name = "ajuste de la aplicación"
        verbose_name_plural = "ajustes de la aplicación"
        ordering = ["origen", "grupo", "orden", "clave"]

    def __str__(self) -> str:
        return f"{self.clave} = {self.valor}"

    @property
    def como_valor(self) -> Any:
        """El valor con su tipo: número, sí/no, lista o texto."""
        if self.tipo == self.Tipo.BOOLEANO:
            return str(self.valor).strip().lower() in ("1", "si", "sí", "true", "on", "yes")
        if self.tipo == self.Tipo.ENTERO:
            try:
                return int(str(self.valor).strip())
            except (TypeError, ValueError):
                return 0
        if self.tipo == self.Tipo.LISTA:
            return tuple(pieza.strip() for pieza in str(self.valor).split(",") if pieza.strip())
        return self.valor


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
