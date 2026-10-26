"""Configuración de la app de roles y permisos."""

from __future__ import annotations

from django.apps import AppConfig

__all__ = ["PersonalizeOptionsConfig"]


class PersonalizeOptionsConfig(AppConfig):
    """Roles y permisos de lectura/escritura por opción, para el lado del cliente.

    Las tablas del paquete las crea el propio paquete: sus migraciones viajan
    dentro (``personalize_options/migrations/``), así que en cualquier proyecto
    basta con poner la app en ``INSTALLED_APPS`` y ejecutar ``migrate``.

    ``default_auto_field`` se fija aquí para que las tablas salgan iguales en
    todos los proyectos, se ponga lo que se ponga en ``DEFAULT_AUTO_FIELD``.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "personalize_options"
    verbose_name = "Configuración y permisos"

    def ready(self) -> None:
        """Deja sembrados los ajustes cada vez que se migra.

        Cada paquete declara los suyos en su propio ``ready()``; el que se ejecuta
        después de ``migrate`` los guarda todos en la tabla ``Ajuste``.
        """
        from django.db.models.signals import post_migrate

        from .ajustes import sembrar_al_migrar

        post_migrate.connect(sembrar_al_migrar, sender=self, dispatch_uid="personalize_options.ajustes")
