"""La tabla de los ajustes, con los del paquete ya puestos.

Es el ``settings.py`` que se cambia sin tocar código: cada paquete declara los
suyos desde su ``ready()`` y, al terminar ``migrate``, la señal ``post_migrate``
los deja sembrados aquí.
"""

from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models

AJUSTES = (
    ("modo", "abierto", "texto", "Seguridad", 1,
     "«abierto»: quien no tenga ningún rol puede todo. «cerrado»: solo lo que los roles permitan."),
    ("superusuarios_todo", "si", "booleano", "Seguridad", 2,
     "Los superusuarios de Django pueden todo, aunque no tengan rol."),
)


def sembrar(apps, schema_editor):
    Ajuste = apps.get_model("personalize_options", "Ajuste")
    for clave, valor, tipo, grupo, orden, descripcion in AJUSTES:
        Ajuste.objects.update_or_create(
            clave=clave,
            defaults={
                "valor": valor,
                "tipo": tipo,
                "grupo": grupo,
                "orden": orden,
                "descripcion": descripcion,
                "editable": True,
            },
        )


def deshacer(apps, schema_editor):
    Ajuste = apps.get_model("personalize_options", "Ajuste")
    Ajuste.objects.filter(clave__in=[fila[0] for fila in AJUSTES]).delete()


class Migration(migrations.Migration):
    dependencies = [("personalize_options", "0005_categorias_de_serie")]

    operations = [
        migrations.CreateModel(
            name="Ajuste",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("clave", models.SlugField(max_length=60, unique=True, verbose_name="clave")),
                ("valor", models.TextField(blank=True, verbose_name="valor")),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("texto", "Texto"),
                            ("entero", "Número entero"),
                            ("booleano", "Sí o no"),
                            ("lista", "Lista separada por comas"),
                        ],
                        default="texto",
                        max_length=10,
                        verbose_name="tipo",
                    ),
                ),
                ("grupo", models.CharField(blank=True, max_length=40, verbose_name="grupo")),
                ("descripcion", models.CharField(blank=True, max_length=220, verbose_name="descripción")),
                ("orden", models.PositiveIntegerField(default=0, verbose_name="orden")),
                ("editable", models.BooleanField(default=True, verbose_name="editable")),
                ("actualizado", models.DateTimeField(auto_now=True, verbose_name="actualizado")),
            ],
            options={
                "verbose_name": "ajuste",
                "verbose_name_plural": "ajustes",
                "ordering": ["grupo", "orden", "clave"],
            },
        ),
        migrations.RunPython(sembrar, deshacer),
    ]
