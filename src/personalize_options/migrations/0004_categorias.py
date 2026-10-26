"""Las categorías de permisos: la tabla y el enlace con las opciones.

Hasta ahora el apartado de una opción era un texto suelto (``Opcion.grupo``). Con
las categorías pasa a ser un registro que se puede crear, renombrar y ordenar sin
tocar código, y el asistente del rol agrupa las casillas por categoría.
"""

from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("personalize_options", "0003_sembrar_opciones"),
    ]

    operations = [
        migrations.CreateModel(
            name="Categoria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=60, unique=True, verbose_name="nombre")),
                (
                    "descripcion",
                    models.CharField(
                        blank=True,
                        help_text="Para qué es esta categoría: lo que se lee bajo el título.",
                        max_length=200,
                        verbose_name="descripción",
                    ),
                ),
                (
                    "orden",
                    models.PositiveSmallIntegerField(
                        default=100,
                        help_text="Con qué orden sale entre las demás categorías.",
                        verbose_name="orden",
                    ),
                ),
                (
                    "icono",
                    models.CharField(
                        blank=True, help_text="El del menú, sin el «mif-».", max_length=40, verbose_name="icono"
                    ),
                ),
                (
                    "activa",
                    models.BooleanField(
                        default=True,
                        help_text="Una categoría apagada no da permisos a las opciones que tenga.",
                        verbose_name="activa",
                    ),
                ),
                ("creado", models.DateTimeField(auto_now_add=True, verbose_name="creada")),
                ("actualizado", models.DateTimeField(auto_now=True, verbose_name="actualizada")),
            ],
            options={
                "verbose_name": "categoría de permisos",
                "verbose_name_plural": "categorías de permisos",
                "ordering": ["orden", "nombre"],
            },
        ),
        migrations.AddField(
            model_name="opcion",
            name="categoria",
            field=models.ForeignKey(
                blank=True,
                help_text="Con qué otras opciones se agrupa en el asistente del rol.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="opciones",
                to="personalize_options.categoria",
                verbose_name="categoría",
            ),
        ),
        migrations.AlterField(
            model_name="opcion",
            name="grupo",
            field=models.CharField(
                blank=True,
                help_text="Se copia de la categoría: es lo que lee el menú.",
                max_length=40,
                verbose_name="apartado",
            ),
        ),
    ]
