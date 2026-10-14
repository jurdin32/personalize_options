"""Las opciones de serie: las pantallas que trae el paquete.

Se siembran al instalar el paquete para que un proyecto recién añadido tenga sus
pantallas protegidas desde el primer día. A partir de ahí mandan los datos: las
opciones se crean, se renombran y se apagan desde la aplicación o el admin, sin
migrar nada.

La lista va copiada aquí a propósito: una migración tiene que hacer siempre lo mismo,
aunque el paquete cambie sus opciones de serie más adelante.
"""

from __future__ import annotations

from django.db import migrations

#: (clave, nombre, apartado), en el orden del menú.
OPCIONES = (
    ("tablero", "Tablero", "Resumen"),
    ("facturar", "Nueva factura", "Facturar"),
    ("facturas", "Facturas emitidas", "Facturar"),
    ("notas_credito", "Notas de crédito", "Comprobantes"),
    ("notas_debito", "Notas de débito", "Comprobantes"),
    ("liquidaciones_compra", "Liquidaciones de compra", "Comprobantes"),
    ("guias_remision", "Guías de remisión", "Comprobantes"),
    ("retenciones", "Retenciones", "Comprobantes"),
    ("productos", "Productos y servicios", "Catálogo"),
    ("clientes", "Clientes", "Catálogo"),
    ("conductores", "Conductores", "Catálogo"),
    ("vehiculos", "Vehículos", "Catálogo"),
    ("inventario", "Inventario", "Catálogo"),
    ("configuracion", "Configuración del SRI", "Sistema"),
    ("roles", "Roles y permisos", "Sistema"),
    ("usuarios", "Usuarios y sus roles", "Sistema"),
    ("opciones", "Opciones de la aplicación", "Sistema"),
)


def sembrar(apps, schema_editor):
    """Crea las opciones de serie que todavía no estén."""
    Opcion = apps.get_model("personalize_options", "Opcion")
    for orden, (clave, nombre, grupo) in enumerate(OPCIONES):
        Opcion.objects.update_or_create(
            clave=clave, defaults={"nombre": nombre, "grupo": grupo, "orden": orden}
        )


def deshacer(apps, schema_editor):
    """Quita las opciones de serie (las que haya creado esta migración)."""
    Opcion = apps.get_model("personalize_options", "Opcion")
    Opcion.objects.filter(clave__in=[clave for clave, _, _ in OPCIONES]).delete()


class Migration(migrations.Migration):
    dependencies = [("personalize_options", "0002_opcion")]

    operations = [migrations.RunPython(sembrar, deshacer)]
