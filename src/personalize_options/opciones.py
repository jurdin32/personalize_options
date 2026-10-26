"""Las opciones de la aplicación: lo que se puede permitir o negar.

Una opción es una pantalla o un apartado del menú. Viven en la **base de datos**
(la tabla ``personalize_options_opcion``), así que se pueden crear, renombrar o
apagar desde la aplicación o desde el admin, sin tocar código y sin migrar. De aquí
salen los permisos que se marcan en cada rol y las opciones que enseña el menú.

Las de serie —``DE_SERIE``, más abajo— son las que siembra la migración de datos al
instalar el paquete: sirven para que un proyecto recién añadido tenga sus pantallas
protegidas desde el primer día. Si la tabla todavía no existe (por estar sin migrar),
se usan éstas, para que la aplicación no se rompa.

La clave es lo que se guarda; para que el menú y las vistas hablen el mismo idioma,
conviene no cambiarla una vez en marcha.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

__all__ = [
    "OpcionDeSerie",
    "DE_SERIE",
    "todas",
    "categorias",
    "grupos",
    "por_clave",
    "de",
    "existe",
    "opciones_de_choices",
]


@dataclass(frozen=True)
class OpcionDeSerie:
    """Una de las opciones que trae el paquete de serie."""

    clave: str
    nombre: str
    grupo: str


#: Las opciones que siembra la migración de datos, en el orden del menú.
DE_SERIE: Tuple[OpcionDeSerie, ...] = (
    OpcionDeSerie("tablero", "Tablero", "Resumen"),
    OpcionDeSerie("facturar", "Nueva factura", "Facturar"),
    OpcionDeSerie("facturas", "Facturas emitidas", "Facturar"),
    OpcionDeSerie("notas_credito", "Notas de crédito", "Comprobantes"),
    OpcionDeSerie("notas_debito", "Notas de débito", "Comprobantes"),
    OpcionDeSerie("liquidaciones_compra", "Liquidaciones de compra", "Comprobantes"),
    OpcionDeSerie("guias_remision", "Guías de remisión", "Comprobantes"),
    OpcionDeSerie("retenciones", "Retenciones", "Comprobantes"),
    OpcionDeSerie("productos", "Productos y servicios", "Catálogo"),
    OpcionDeSerie("clientes", "Clientes", "Catálogo"),
    OpcionDeSerie("conductores", "Conductores", "Catálogo"),
    OpcionDeSerie("vehiculos", "Vehículos", "Catálogo"),
    OpcionDeSerie("inventario", "Inventario", "Catálogo"),
    OpcionDeSerie("configuracion", "Configuración del SRI", "Sistema"),
    OpcionDeSerie("roles", "Roles y permisos", "Sistema"),
    OpcionDeSerie("usuarios", "Usuarios y sus roles", "Sistema"),
    OpcionDeSerie("opciones", "Opciones de la aplicación", "Sistema"),
)


def _modelo() -> Any:
    """El modelo de las opciones.

    Se importa al usarlo porque ``models.py`` usa este módulo: traerlo aquí arriba
    sería un círculo.
    """
    from .models import Opcion

    return Opcion


def _las_de_serie() -> List[OpcionDeSerie]:
    """Las de serie, listas para usar si la tabla todavía no está."""
    return list(DE_SERIE)


def todas(solo_activas: bool = False) -> List[Any]:
    """Las opciones de la aplicación, en orden.

    Si la tabla no existe (paquete recién añadido, sin migrar), devuelve las de
    serie: la aplicación sigue funcionando y protege sus pantallas.
    """
    from django.db.utils import DatabaseError, OperationalError, ProgrammingError

    try:
        consulta = _modelo().objects.all()
        if solo_activas:
            consulta = consulta.filter(activo=True)
        return list(consulta)
    except (DatabaseError, OperationalError, ProgrammingError):
        return _las_de_serie()


def categorias(solo_activas: bool = False) -> List[Any]:
    """Las categorías de permisos, en su orden.

    Si la tabla todavía no existe, devuelve una por cada apartado de las opciones de
    serie: el asistente del rol se pinta igual.
    """
    from django.db.utils import DatabaseError, OperationalError, ProgrammingError

    from .models import Categoria

    try:
        consulta = Categoria.objects.all()
        if solo_activas:
            consulta = consulta.filter(activa=True)
        return list(consulta)
    except (DatabaseError, OperationalError, ProgrammingError):
        return []


def grupos(solo_activas: bool = False) -> List[Tuple[str, List[Any]]]:
    """Las opciones por **categoría**, en el orden de la categoría.

    Dentro de cada categoría las opciones salen por su ``orden``, que es el mismo que
    se ve en el menú; entre categorías manda el ``orden`` de la categoría. Las
    opciones que no tengan categoría se agrupan por su apartado y van al final, para
    que una opción vieja no se pierda por el camino.
    """
    por_categoria: Dict[str, List[Any]] = {}
    ordenes: Dict[str, int] = {}
    for opcion in sorted(todas(solo_activas=solo_activas), key=lambda o: o.orden):
        nombre = opcion.categoria_nombre
        por_categoria.setdefault(nombre, []).append(opcion)
        ordenes[nombre] = min(ordenes.get(nombre, 10**6), opcion.categoria_orden)
    return sorted(por_categoria.items(), key=lambda par: (ordenes[par[0]], par[0]))


def por_clave(solo_activas: bool = False) -> Dict[str, Any]:
    """La opción de cada clave."""
    return {opcion.clave: opcion for opcion in todas(solo_activas=solo_activas)}


def existe(clave: str) -> bool:
    """¿Esa clave es una opción de la aplicación?"""
    return clave in por_clave()


def de(clave: str) -> Any:
    """La opción de esa clave (lanza ``KeyError`` si no existe)."""
    encontrada = por_clave().get(clave)
    if encontrada is None:
        raise KeyError(clave)
    return encontrada


def opciones_de_choices() -> List[Tuple[str, str]]:
    """Las opciones como ``choices`` de un campo (con el apartado delante)."""
    return [(opcion.clave, str(opcion)) for opcion in todas()]
