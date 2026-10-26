"""El admin de la seguridad: crear roles y marcar qué puede cada uno.

Un rol se crea y se le marcan sus opciones (lectura o lectura y escritura) en la
misma pantalla; el formulario trae una casilla por opción, agrupadas por apartado.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

from django.contrib import admin
from django.db.models import Count, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce

from . import opciones as registro
from .forms import RolForm
from .models import Ajuste, Categoria, Nivel, Opcion, Permiso, Rol

__all__ = ["CategoriaAdmin", "RolAdmin", "PermisoAdmin", "OpcionAdmin"]


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    """El catálogo de opciones: las pantallas que se pueden permitir o negar.

    Se crean aquí (o desde la aplicación) y con eso ya salen en el asistente de los
    roles y, si llevan dirección, en el menú. No hace falta tocar código ni migrar.
    """

    list_display = ("nombre", "categoria", "clave", "activo", "en_menu", "cuantos_permisos")
    list_editable = ("activo",)
    list_filter = ("categoria", "activo", "en_menu")
    search_fields = ("clave", "nombre", "grupo")
    ordering = ("orden", "nombre")
    list_per_page = 50
    prepopulated_fields = {"clave": ("nombre",)}
    save_on_top = True

    def get_queryset(self, request: Any) -> Any:
        """Cuenta en cuántos roles está marcada cada opción.

        El permiso guarda la **clave** de la opción en un ``CharField`` (no es una
        foránea), así que el conteo va con una subconsulta y no con un ``JOIN``.
        """
        marcadas = (
            Permiso.objects.filter(opcion=OuterRef("clave"))
            .values("opcion")
            .annotate(cuantos=Count("pk"))
            .values("cuantos")
        )
        return super().get_queryset(request).annotate(
            _permisos=Coalesce(Subquery(marcadas, output_field=IntegerField()), 0)
        )

    @admin.display(description="Roles", ordering="_permisos")
    def cuantos_permisos(self, obj: Opcion) -> int:
        """En cuántos roles está marcada esta opción."""
        return Permiso.objects.filter(opcion=obj.clave).count()


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    """La tabla de permisos tal cual: una fila por rol y opción.

    Los permisos se marcan desde el rol (ver :class:`RolAdmin`), que es como se
    piensa un rol; esta pantalla está para poder mirar la tabla —y retocar una fila
    suelta— cuando haga falta.
    """

    list_display = ("rol", "opcion_mostrada", "nivel")
    list_editable = ("nivel",)
    list_filter = ("nivel", "rol")
    search_fields = ("rol__nombre", "opcion")
    list_select_related = ("rol",)
    list_per_page = 50
    ordering = ("rol__nombre", "opcion")
    save_on_top = True

    @admin.display(description="opción", ordering="opcion")
    def opcion_mostrada(self, obj: Permiso) -> str:
        """El nombre de la opción (que no está en la tabla, se declara en opciones.py)."""
        return obj.descripcion_opcion


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    """Roles de la aplicación, con sus permisos por opción."""

    form = RolForm
    list_display = ("nombre", "descripcion", "activo", "cuantos_usuarios", "cuantas_opciones")
    list_filter = ("activo",)
    search_fields = ("nombre", "descripcion", "usuarios__username", "usuarios__first_name")
    filter_horizontal = ("usuarios",)
    list_per_page = 50
    ordering = ("nombre",)
    save_on_top = True
    actions = ("todo_lectura", "todo_escritura", "quitar_todo")

    def get_queryset(self, request: Any) -> Any:
        return (
            super().get_queryset(request)
            .annotate(_usuarios=Count("usuarios", distinct=True), _opciones=Count("permisos", distinct=True))
        )

    def get_form(self, request: Any, obj: Optional[Rol] = None, change: bool = False, **kwargs: Any) -> Any:
        """El formulario del rol trae sus propios campos, no los del modelo.

        Además de los del rol, el formulario pone una casilla por opción (ver
        :class:`~personalize_options.forms.RolForm`), y esas casillas no son campos
        del modelo: el admin no las conoce y se queja, así que se le quita de las
        manos la lista de campos —los *fieldsets* se siguen usando para pintarlos,
        pero los campos los pone el formulario—.
        """
        kwargs["fields"] = None
        return super().get_form(request, obj, change=change, **kwargs)

    def get_fieldsets(self, request: Any, obj: Optional[Rol] = None) -> Tuple:
        """Lo del rol y, debajo, sus opciones por apartado."""
        return tuple(
            [
                (
                    "El rol",
                    {
                        "fields": ("nombre", "descripcion", "activo", "usuarios"),
                        "description": "Póngale nombre y añada los usuarios que lo "
                                       "llevan. Debajo se marca, opción por opción, "
                                       "qué puede hacer cada uno.",
                    },
                )
            ]
            + [
                (grupo, {"fields": tuple(f"nivel_{opcion.clave}" for opcion in opciones)})
                for grupo, opciones in registro.grupos()
            ]
        )

    @admin.display(description="Usuarios", ordering="_usuarios")
    def cuantos_usuarios(self, obj: Rol) -> int:
        return getattr(obj, "_usuarios", 0) or 0

    @admin.display(description="Opciones", ordering="_opciones")
    def cuantas_opciones(self, obj: Rol) -> int:
        return getattr(obj, "_opciones", 0) or 0

    # --------------------------------------------------------------- acciones

    def _marcar(self, roles: Any, nivel: str) -> None:
        for rol in roles:
            for opcion in registro.todas():
                Permiso.objects.update_or_create(
                    rol=rol, opcion=opcion.clave, defaults={"nivel": nivel}
                )

    @admin.action(description="Dar solo lectura en todas las opciones")
    def todo_lectura(self, request: Any, queryset: Any) -> None:
        self._marcar(queryset, Nivel.LECTURA.value)
        self.message_user(request, "Se dio solo lectura en todas las opciones.")

    @admin.action(description="Dar lectura y escritura en todas las opciones")
    def todo_escritura(self, request: Any, queryset: Any) -> None:
        self._marcar(queryset, Nivel.ESCRITURA.value)
        self.message_user(request, "Se dio lectura y escritura en todas las opciones.")

    @admin.action(description="Quitar todos los permisos")
    def quitar_todo(self, request: Any, queryset: Any) -> None:
        Permiso.objects.filter(rol__in=queryset).delete()
        self.message_user(request, "Se quitaron todos los permisos de esos roles.")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Las categorías de permisos: cómo se agrupan las opciones en el asistente."""

    list_display = ("nombre", "orden", "activa", "cuantas_opciones")
    list_editable = ("orden", "activa")
    search_fields = ("nombre", "descripcion")
    ordering = ("orden", "nombre")

    @admin.display(description="opciones")
    def cuantas_opciones(self, objeto: Any) -> int:
        return objeto.opciones.count()


@admin.register(Ajuste)
class AjusteAdmin(admin.ModelAdmin):
    """Los ajustes de la aplicación: el ``settings.py`` que se cambia sin tocar código.

    La clave **no** se edita: es la que lee el código. Tampoco el tipo, el grupo
    ni la descripción, que vienen de la declaración del paquete y se refrescan al
    migrar. Lo único que se escribe a mano es el **valor**, que es el ajuste.
    """

    list_display = ("clave", "origen", "grupo", "valor", "tipo", "actualizado")
    list_filter = ("origen", "grupo", "tipo")
    search_fields = ("clave", "valor", "descripcion", "origen")
    ordering = ("origen", "grupo", "orden", "clave")
    readonly_fields = (
        "clave",
        "origen",
        "tipo",
        "grupo",
        "descripcion",
        "orden",
        "editable",
        "actualizado",
    )
    fields = (
        "clave",
        "origen",
        "grupo",
        "tipo",
        "descripcion",
        "valor",
        "orden",
        "editable",
        "actualizado",
    )
    list_display_links = ("clave",)
    save_on_top = True
    list_per_page = 100

    def has_add_permission(self, request):
        # Los ajustes los declara cada paquete; se cambian, no se inventan.
        return False

    def has_delete_permission(self, request, obj=None):
        # Y tampoco se borran: volverían a aparecer al migrar.
        return False
