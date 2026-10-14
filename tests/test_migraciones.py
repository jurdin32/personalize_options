"""Las migraciones viajan dentro del paquete, y al día.

Las tablas del paquete las crea el propio paquete: al añadirlo a un proyecto y
migrar aparecen los roles y los permisos. Esto vigila que las migraciones que van
dentro correspondan con los modelos, que es lo que hace que «añadir el paquete y
migrar» funcione en cualquier proyecto.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from personalize_options import migrations as las_migraciones
from personalize_options.models import Permiso
from personalize_options.opciones import por_clave


class PruebasDeLasMigraciones(TestCase):
    """El paquete se migra solo: en el proyecto no hay nada que generar."""

    def test_las_migraciones_estan_al_dia_con_los_modelos(self) -> None:
        try:
            call_command(
                "makemigrations",
                "personalize_options",
                check=True,
                dry_run=True,
                stdout=StringIO(),
                stderr=StringIO(),
            )
        except SystemExit:
            self.fail(
                "Hay cambios en los modelos sin migración: ejecute makemigrations "
                "personalize_options dentro del paquete."
            )

    def test_las_migraciones_van_dentro_del_paquete(self) -> None:
        carpeta = Path(las_migraciones.__file__).parent

        self.assertTrue(list(carpeta.glob("0*.py")), f"No hay migraciones en {carpeta}")

    def test_añadir_o_quitar_opciones_no_necesita_migracion(self) -> None:
        # Las opciones no son columnas ni «choices» guardados, sino la lista de
        # opciones.py: se pueden cambiar cuando haga falta sin tocar la base.
        campo = Permiso._meta.get_field("opcion")

        self.assertIsNone(campo.choices)
        self.assertIn(
            "validar_opcion",
            [getattr(validador, "__name__", "") for validador in campo.validators],
        )

        # Lo que se guarda es la clave de la opción, tal cual.
        self.assertIn("clientes", por_clave())
