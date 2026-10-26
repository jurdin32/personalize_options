"""Las categorías que ya existían, sacadas de los apartados de las opciones.

Cada apartado que hubiera pasa a ser una categoría con el mismo nombre, en el orden
en que estaban las opciones, y sus opciones quedan dentro. El campo ``grupo`` no se
toca: el menú lo sigue leyendo, y desde ahora se copia solo de la categoría.
"""

from __future__ import annotations

from django.db import migrations

#: El orden con el que nacen las categorías conocidas. Las que no estén aquí se
#: ponen detrás, con el orden en que aparezcan.
ORDEN = {
    "Resumen": 10,
    "Facturar": 20,
    "Comprobantes": 30,
    "Catálogo": 40,
    "Caja": 45,
    "Contabilidad": 50,
    "Reportes": 60,
    "Sistema": 70,
    "Ayuda": 80,
}

#: Para qué es cada categoría, cuando se sabe.
DESCRIPCION = {
    "Resumen": "El tablero del día.",
    "Facturar": "Emitir facturas y ver las que ya salieron.",
    "Comprobantes": "Los demás comprobantes electrónicos del SRI.",
    "Catálogo": "Clientes, productos, conductores, vehículos e inventario.",
    "Caja": "El efectivo del turno: apertura, movimientos y cierre.",
    "Contabilidad": "Plan de cuentas, asientos, estados financieros y anexos.",
    "Reportes": "Los reportes y las estadísticas, uno por uno.",
    "Sistema": "La configuración del SRI, los usuarios y las opciones.",
    "Ayuda": "El manual de uso del sistema.",
}

ICONO = {
    "Resumen": "dashboard",
    "Facturar": "receipt",
    "Comprobantes": "description",
    "Catálogo": "folder",
    "Caja": "money",
    "Contabilidad": "balance",
    "Reportes": "charts",
    "Sistema": "cog",
    "Ayuda": "help",
}


def sembrar(apps, schema_editor):
    Categoria = apps.get_model("personalize_options", "Categoria")
    Opcion = apps.get_model("personalize_options", "Opcion")

    apartados = []
    for opcion in Opcion.objects.order_by("orden", "pk"):
        if opcion.grupo and opcion.grupo not in apartados:
            apartados.append(opcion.grupo)

    for posicion, nombre in enumerate(apartados):
        categoria, _ = Categoria.objects.get_or_create(
            nombre=nombre,
            defaults={
                "descripcion": DESCRIPCION.get(nombre, ""),
                "orden": ORDEN.get(nombre, 100 + posicion),
                "icono": ICONO.get(nombre, ""),
                "activa": True,
            },
        )
        Opcion.objects.filter(grupo=nombre, categoria__isnull=True).update(categoria=categoria)


def deshacer(apps, schema_editor):
    Categoria = apps.get_model("personalize_options", "Categoria")
    Opcion = apps.get_model("personalize_options", "Opcion")

    for categoria in Categoria.objects.all():
        Opcion.objects.filter(categoria=categoria).update(grupo=categoria.nombre, categoria=None)
    Categoria.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("personalize_options", "0004_categorias"),
    ]

    operations = [migrations.RunPython(sembrar, deshacer)]
