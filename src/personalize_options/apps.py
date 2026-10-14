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
    verbose_name = "Seguridad (roles y permisos)"
